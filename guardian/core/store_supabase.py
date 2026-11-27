"""SupabaseStore: archivio condiviso. Ogni sessione Streamlit ha il proprio client autenticato (RLS lato DB)."""
from __future__ import annotations

from .models import APPROVAL_STATI, Handoff, ValidazioneError, adesso, pulisci, pulisci_file, scegli
from .store import _valida_task, hash_token, nuovo_token


class SupabaseStore:
    """Archivio condiviso su Supabase. Ogni sessione Streamlit ha il proprio client autenticato."""

    modalita = "supabase"

    def __init__(self, url: str, anon_key: str):
        from supabase import create_client  # import pigro: non serve in modalità locale
        self._c = create_client(url, anon_key)
        self.user: dict | None = None

    def login(self, email: str, password: str) -> dict:
        email = (email or "").strip().lower()
        self._c.auth.sign_in_with_password({"email": email, "password": password})
        r = self._c.table("users").select("*").eq("email", email).eq("stato", "attivo").execute().data
        if not r:
            self._c.auth.sign_out()
            raise PermissionError("Questo account non è tra i collaboratori autorizzati di Guardian.")
        self.user = r[0]
        return self.user

    def logout(self) -> None:
        self._c.auth.sign_out()
        self.user = None

    def _t(self, nome):
        return self._c.table(nome)

    def users(self):
        return self._t("users").select("*").order("id").execute().data

    def devices(self):
        return self._t("devices").select("id,user_id,nome,agent_name,model,stato,current_task_id,error,limit_reached,"
                                         "last_seen,last_checkpoint,created_at").order("user_id").execute().data

    # token_hash non è leggibile (vedi migrazione): insert/update senza "returning" della riga.
    def register_device(self, user_id, nome, agent_name=""):
        from postgrest.types import ReturnMethod
        token = nuovo_token()
        nome = pulisci(nome, 80, True, "nome dispositivo")
        self._t("devices").insert({"user_id": user_id, "nome": nome, "agent_name": pulisci(agent_name, 80) or None,
                                   "token_hash": hash_token(token)}, returning=ReturnMethod.minimal).execute()
        d = [x for x in self.devices() if x["user_id"] == user_id and x["nome"] == nome]
        return (max(d, key=lambda x: x["id"]) if d else {"nome": nome, "user_id": user_id}), token

    def revoke_device(self, device_id):
        from postgrest.types import ReturnMethod
        self._t("devices").update({"token_hash": hash_token(nuovo_token()), "stato": "offline"},
                                  returning=ReturnMethod.minimal).eq("id", device_id).execute()

    def tasks(self, stato=None):
        q = self._t("tasks").select("*")
        if stato:
            q = q.eq("stato", stato)
        return q.order("updated_at", desc=True).execute().data

    def task(self, task_id):
        r = self._t("tasks").select("*").eq("id", task_id).execute().data
        return r[0] if r else None

    def create_task(self, titolo, descrizione="", responsabile=None, agente="", priorita="media", next_step="",
                    created_by=None):
        campi = _valida_task({"titolo": titolo, "descrizione": descrizione, "responsabile": responsabile,
                              "agente": agente, "priorita": priorita, "next_step": next_step})
        t = self._t("tasks").insert({**campi, "created_by": created_by}).execute().data[0]
        self.add_event("task_creato", f"Creato task: {campi['titolo']}", user_id=created_by, task_id=t["id"])
        return t

    def update_task(self, task_id, by=None, agent_name=None, device_id=None, **campi):
        campi = _valida_task(campi)
        if not campi:
            raise ValidazioneError("Nessuna modifica.")
        r = self._t("tasks").update(campi).eq("id", task_id).execute().data
        if not r:
            raise ValidazioneError("Task inesistente.")
        descr = ", ".join(f"{k}={v}" for k, v in campi.items() if k in ("stato", "priorita", "responsabile", "agente"))
        self.add_event("task_aggiornato", f"Task #{task_id} aggiornato{': ' + descr if descr else ''}", user_id=by,
                       agent_name=agent_name, task_id=task_id, files=campi.get("files_changed") or [])
        return r[0]

    def events(self, limit=100, task_id=None):
        q = self._t("activity_events").select("*")
        if task_id:
            q = q.eq("task_id", task_id)
        return q.order("timestamp", desc=True).limit(limit).execute().data

    def add_event(self, event_type, message, user_id=None, agent_name=None, task_id=None, device_id=None,
                  files=None, external_key=None, timestamp=None):
        row = {"event_type": pulisci(event_type, 40, True, "tipo evento"), "message": pulisci(message, 1000, True, "messaggio"),
               "user_id": user_id, "agent_name": agent_name, "task_id": task_id, "device_id": device_id,
               "files": pulisci_file(files), "external_key": external_key}
        if timestamp:
            row["timestamp"] = timestamp
        self._t("activity_events").insert(row).execute()
        return True

    def handoffs(self, task_id=None, limit=50):
        q = self._t("handoffs").select("*")
        if task_id:
            q = q.eq("task_id", task_id)
        return q.order("timestamp", desc=True).limit(limit).execute().data

    def add_handoff(self, h: Handoff, device_id=None, user_id=None):
        h.valida()
        r = self._t("handoffs").insert({"task_id": h.task_id, "device_id": device_id, "agent_name": h.agent_name,
                                        "summary": h.summary, "completed_steps": h.completed_steps,
                                        "files_changed": h.files_changed, "decisions": h.decisions,
                                        "errors": h.errors, "tests": h.tests, "next_step": h.next_step}).execute().data[0]
        if h.task_id:
            self._t("tasks").update({"next_step": h.next_step}).eq("id", h.task_id).execute()
        self.add_event("checkpoint", f"Handoff salvato. Prossimo passo: {h.next_step}", user_id=user_id,
                       agent_name=h.agent_name, task_id=h.task_id, files=h.files_changed)
        return r["id"]

    def approvals(self, status=None):
        q = self._t("approvals").select("*")
        if status:
            q = q.eq("status", status)
        return q.order("created_at", desc=True).execute().data

    def request_approval(self, action, description="", task_id=None, requested_by=None):
        r = self._t("approvals").insert({"task_id": task_id, "action": pulisci(action, 200, True, "azione"),
                                         "description": pulisci(description, 2000),
                                         "requested_by": requested_by}).execute().data[0]
        self.add_event("approvazione_richiesta", f"Richiesta approvazione: {action}", user_id=requested_by,
                       task_id=task_id)
        return r["id"]

    def decide_approval(self, approval_id, status, decided_by):
        status = scegli(status, APPROVAL_STATI[1:], "Decisione")
        self._t("approvals").update({"status": status, "decided_by": decided_by, "decided_at": adesso()}) \
            .eq("id", approval_id).eq("status", "richiesta").execute()
        self.add_event("approvazione_decisa", f"Approvazione #{approval_id}: {status}", user_id=decided_by)
