"""SupabaseStore: archivio condiviso. Ogni sessione Streamlit ha il proprio client autenticato (RLS lato DB).

Differenza con SqliteStore: notifiche, needs_approval/ready dopo le approvazioni e controllo delle dipendenze
li fanno i trigger della migrazione 002, quindi qui non vengono ripetuti. Gli eventi della timeline li scrive Python
in entrambi i casi.
"""
from __future__ import annotations

from .models import (ACTION_TYPES, AGENT_STATI, AGENT_TIPI, APPROVAL_STATI, Handoff, ValidazioneError, adesso, pulisci,
                     pulisci_file, scegli)
from .store import (STATI_PIANO, _valida_task, hash_token, messaggio_db, nuovo_token, severita, testo_ripresa,
                    valida_memoria)

COLONNE_DEVICES = ("id,user_id,nome,agent_name,model,stato,current_task_id,error,limit_reached,last_seen,"
                   "last_checkpoint,created_at")


class SupabaseStore:
    modalita = "supabase"

    def __init__(self, url: str, anon_key: str):
        from supabase import create_client  # import pigro: non serve in modalità locale
        self._c = create_client(url, anon_key)
        self.user: dict | None = None

    # --- accesso ----------------------------------------------------------------
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

    # --- utilità ------------------------------------------------------------------
    def _t(self, nome):
        return self._c.table(nome)

    @staticmethod
    def _ex(query):
        """Esegue una query traducendo gli errori di vincolo/trigger in ValidazioneError leggibili."""
        try:
            return query.execute().data
        except Exception as e:  # postgrest.APIError e simili
            msg = messaggio_db(e)
            if msg:
                raise ValidazioneError(msg) from None
            raise

    @staticmethod
    def _minimal():
        from postgrest.types import ReturnMethod
        return ReturnMethod.minimal

    def ping(self) -> bool:
        self._ex(self._t("users").select("id").limit(1))
        return True

    # --- utenti e notifiche ---------------------------------------------------------
    def users(self):
        return self._ex(self._t("users").select("id,nome,ruolo,agente,stato,accesso").order("id"))

    def notifications(self, user_id, solo_non_lette=False, limit=50):
        q = self._t("notifications").select("*").eq("user_id", user_id)
        if solo_non_lette:
            q = q.is_("read_at", "null")
        return self._ex(q.order("created_at", desc=True).limit(limit))

    def mark_read(self, user_id, notification_id=None):
        q = self._t("notifications").update({"read_at": adesso()}, returning=self._minimal()).eq("user_id", user_id)
        q = q.eq("id", notification_id) if notification_id else q.is_("read_at", "null")
        self._ex(q)

    # --- progetti -------------------------------------------------------------------
    def projects(self, solo_attivi=False):
        q = self._t("projects").select("*")
        if solo_attivi:
            q = q.eq("stato", "attivo")
        return self._ex(q.order("nome"))

    def create_project(self, nome, descrizione="", created_by=None):
        try:
            p = self._ex(self._t("projects").insert({"nome": pulisci(nome, 120, True, "nome progetto"),
                                                     "descrizione": pulisci(descrizione, 2000) or None,
                                                     "created_by": created_by}))[0]
        except Exception as e:
            if "projects_nome_uniq" in str(e):
                raise ValidazioneError("Esiste già un progetto con questo nome.") from None
            raise
        self.add_event("project_created", f"Creato progetto: {nome}", user_id=created_by, project_id=p["id"])
        return p

    def update_project(self, project_id, stato):
        self._ex(self._t("projects").update({"stato": scegli(stato, ("attivo", "archiviato"), "Stato progetto")})
                 .eq("id", project_id))

    # --- dispositivi e agenti -------------------------------------------------------
    def devices(self):
        return self._ex(self._t("devices").select(COLONNE_DEVICES).order("user_id"))

    # token_hash non è leggibile (vedi migrazioni): insert/update senza "returning" della riga.
    def register_device(self, user_id, nome, agent_name=""):
        token = nuovo_token()
        nome = pulisci(nome, 80, True, "nome dispositivo")
        self._ex(self._t("devices").insert({"user_id": user_id, "nome": nome,
                                            "agent_name": pulisci(agent_name, 80) or None,
                                            "token_hash": hash_token(token)}, returning=self._minimal()))
        d = [x for x in self.devices() if x["user_id"] == user_id and x["nome"] == nome]
        return (max(d, key=lambda x: x["id"]) if d else {"nome": nome, "user_id": user_id}), token

    def revoke_device(self, device_id):
        self._ex(self._t("devices").update({"token_hash": hash_token(nuovo_token()), "stato": "offline"},
                                           returning=self._minimal()).eq("id", device_id))

    def agents(self):
        return self._ex(self._t("agents").select("*").order("user_id").order("id"))

    def agent(self, agent_id):
        r = self._ex(self._t("agents").select("*").eq("id", agent_id))
        return r[0] if r else None

    def upsert_agent(self, id, user_id, nome, tipo, device_id=None, capabilities=(), disponibile=True):
        caps = sorted({pulisci(c, 40) for c in (capabilities or []) if c and c.strip()})
        return self._ex(self._t("agents").upsert({
            "id": pulisci(id, 60, True, "id agente").lower(), "user_id": user_id, "device_id": device_id,
            "nome": pulisci(nome, 80, True, "nome agente"), "tipo": scegli(tipo, AGENT_TIPI, "Tipo agente"),
            "capabilities": caps, "disponibile": bool(disponibile)}))[0]

    def set_agent_state(self, agent_id, stato, current_task_id=None, error=None, by=None, manuale=True):
        a = self.agent(agent_id)
        if not a:
            raise ValidazioneError("Agente inesistente.")
        stato = scegli(stato, AGENT_STATI, "Stato agente")
        err = pulisci(error, 500, nome="errore") or None
        r = self._ex(self._t("agents").update({"stato": stato, "current_task_id": current_task_id, "error": err,
                                               "last_activity": adesso()}).eq("id", agent_id))[0]
        if a["stato"] != stato or err:
            self.add_event("agent_state", f"{a['nome']}: {stato}{' (manuale)' if manuale else ''}"
                           + (f" — {err}" if err else ""), user_id=by or a["user_id"], agent_id=agent_id,
                           agent_name=a["nome"], task_id=current_task_id,
                           severity="error" if stato == "error" else "info")
        return r

    def agent_logs(self, agent_id=None, device_id=None, project_id=None, task_id=None, level=None, dal=None, al=None,
                   limit=200):
        q = self._t("agent_logs").select("*")
        for col, val in (("agent_id", agent_id), ("device_id", device_id), ("project_id", project_id),
                         ("task_id", task_id), ("level", level)):
            if val not in (None, ""):
                q = q.eq(col, val)
        if dal:
            q = q.gte("ts", dal)
        if al:
            q = q.lte("ts", al)
        return self._ex(q.order("ts", desc=True).limit(limit))

    # --- task -----------------------------------------------------------------------
    def tasks(self, stato=None, project_id=None):
        q = self._t("tasks").select("*")
        if stato:
            q = q.eq("stato", stato)
        if project_id:
            q = q.eq("project_id", project_id)
        return self._ex(q.order("updated_at", desc=True))

    def task(self, task_id):
        r = self._ex(self._t("tasks").select("*").eq("id", task_id))
        return r[0] if r else None

    def create_task(self, titolo, descrizione="", responsabile=None, agente="", priorita="media", next_step="",
                    created_by=None, stato="backlog", project_id=None, depends_on=(), assigned_agent_id=None,
                    expected_result=None, completion_criteria=None, plan_id=None):
        campi = _valida_task({"titolo": titolo, "descrizione": descrizione, "responsabile": responsabile,
                              "agente": agente, "priorita": priorita, "next_step": next_step, "stato": stato,
                              "project_id": project_id, "depends_on": list(depends_on or []),
                              "assigned_agent_id": assigned_agent_id, "expected_result": expected_result,
                              "completion_criteria": completion_criteria, "plan_id": plan_id})
        t = self._ex(self._t("tasks").insert({**campi, "created_by": created_by}))[0]
        self.add_event("task_created", f"Creato task: {campi['titolo']}", user_id=created_by, task_id=t["id"],
                       project_id=campi["project_id"])
        if campi["assigned_agent_id"]:
            self.add_event("task_assigned", f"Task #{t['id']} assegnato a {campi['assigned_agent_id']}",
                           user_id=created_by, task_id=t["id"], agent_id=campi["assigned_agent_id"],
                           project_id=campi["project_id"])
        return t

    def update_task(self, task_id, by=None, agent_name=None, device_id=None, agent_id=None, **campi):
        campi = _valida_task(campi)
        prima = self.task(task_id)
        if not campi or not prima:
            raise ValidazioneError("Task inesistente o nessuna modifica.")
        dopo = self._ex(self._t("tasks").update(campi).eq("id", task_id))[0]
        tid, comune = dopo["id"], dict(user_id=by, agent_name=agent_name, task_id=dopo["id"], device_id=device_id,
                                       project_id=dopo.get("project_id"),
                                       agent_id=agent_id or dopo.get("assigned_agent_id"))
        if dopo.get("assigned_agent_id") != prima.get("assigned_agent_id") and dopo.get("assigned_agent_id"):
            self.add_event("task_assigned", f"Task #{tid} assegnato a {dopo['assigned_agent_id']}", **comune)
        if dopo["stato"] != prima["stato"]:
            tipo = {"running": "task_started", "completed": "task_completed", "failed": "task_failed"}.get(
                dopo["stato"], "task_updated")
            self.add_event(tipo, f"Task #{tid} {prima['stato']} → {dopo['stato']}",
                           severity="error" if dopo["stato"] == "failed" else "info",
                           files=dopo.get("files_changed") or [], **comune)
        elif any(dopo.get(k) != prima.get(k) for k in ("priorita", "responsabile", "next_step", "files_changed",
                                                      "result", "error", "depends_on")):
            self.add_event("task_updated", f"Task #{tid} aggiornato", files=dopo.get("files_changed") or [], **comune)
        return dopo

    # --- eventi ---------------------------------------------------------------------
    def events(self, limit=100, task_id=None):
        q = self._t("activity_events").select("*")
        if task_id:
            q = q.eq("task_id", task_id)
        return self._ex(q.order("timestamp", desc=True).limit(limit))

    def add_event(self, event_type, message, user_id=None, agent_name=None, task_id=None, device_id=None,
                  files=None, external_key=None, timestamp=None, severity="info", agent_id=None, project_id=None):
        row = {"event_type": pulisci(event_type, 40, True, "tipo evento"), "message": pulisci(message, 1000, True, "messaggio"),
               "user_id": user_id, "agent_name": agent_name, "task_id": task_id, "device_id": device_id,
               "files": pulisci_file(files), "external_key": external_key, "severity": severita(severity),
               "agent_id": agent_id, "project_id": project_id}
        if timestamp:
            row["timestamp"] = timestamp
        self._ex(self._t("activity_events").insert(row, returning=self._minimal()))
        return True

    # --- handoff --------------------------------------------------------------------
    def handoffs(self, task_id=None, limit=50):
        q = self._t("handoffs").select("*")
        if task_id:
            q = q.eq("task_id", task_id)
        return self._ex(q.order("timestamp", desc=True).limit(limit))

    def add_handoff(self, h: Handoff, device_id=None, user_id=None):
        """Le notifiche al destinatario le crea il trigger handoffs_notifica (migrazione 004)."""
        h.valida()
        r = self._ex(self._t("handoffs").insert({
            "task_id": h.task_id, "device_id": device_id, "agent_name": h.agent_name, "summary": h.summary,
            "files_changed": h.files_changed, "next_step": h.next_step, "from_agent_id": h.from_agent_id,
            "to_agent_id": h.to_agent_id, "stato": "aperto", **{k: getattr(h, k) for k in Handoff.TESTI}}))[0]
        t = None
        if h.task_id:
            t = self._ex(self._t("tasks").update({"next_step": h.next_step}).eq("id", h.task_id))[0]
            self.add_memory("ripresa", testo_ripresa(h), f"handoff #{r['id']}", t.get("project_id"), h.task_id, user_id)
        self.add_event("handoff" if h.to_agent_id else "checkpoint",
                       f"Handoff salvato{' → ' + h.to_agent_id if h.to_agent_id else ''}. Prossimo passo: {h.next_step}",
                       user_id=user_id, agent_name=h.agent_name, agent_id=h.from_agent_id, task_id=h.task_id,
                       files=h.files_changed, project_id=t.get("project_id") if t else None)
        return r["id"]

    def handoff(self, handoff_id):
        r = self._ex(self._t("handoffs").select("*").eq("id", handoff_id))
        return r[0] if r else None

    def take_handoff(self, handoff_id, agent_id=None, by=None):
        campi = {"stato": "preso", **({"to_agent_id": agent_id} if agent_id else {})}
        r = self._ex(self._t("handoffs").update(campi).eq("id", handoff_id).eq("stato", "aperto"))
        if not r:
            raise ValidazioneError("Handoff inesistente o già preso.")
        self.add_event("handoff_taken", f"Handoff #{handoff_id} preso" + (f" da {agent_id}" if agent_id else ""),
                       user_id=by, agent_id=agent_id, task_id=r[0].get("task_id"))
        return r[0]

    def close_handoff(self, handoff_id, by=None):
        r = self._ex(self._t("handoffs").update({"stato": "chiuso"}).eq("id", handoff_id).neq("stato", "chiuso"))
        if not r:
            raise ValidazioneError("Handoff inesistente o già chiuso.")
        self.add_event("handoff_closed", f"Handoff #{handoff_id} chiuso", user_id=by, task_id=r[0].get("task_id"))
        return r[0]

    def memories(self, project_id=None, task_id=None, kind=None, q=None, includi_superate=False, limit=100):
        sel = self._t("memory").select("id,project_id,task_id,kind,content,source,created_by,created_at,superseded_by")
        for col, val in (("project_id", project_id), ("task_id", task_id), ("kind", kind)):
            if val not in (None, ""):
                sel = sel.eq(col, val)
        if not includi_superate:
            sel = sel.is_("superseded_by", "null")
        if q and q.strip():
            sel = sel.text_search("ricerca", q.strip(), options={"config": "italian", "type": "plain"})
        return self._ex(sel.order("created_at", desc=True).limit(limit))

    def add_memory(self, kind, content, source, project_id=None, task_id=None, created_by=None):
        campi = valida_memoria(kind, content, source)
        return self._ex(self._t("memory").insert({**campi, "project_id": project_id, "task_id": task_id,
                                                  "created_by": created_by}))[0]["id"]

    def supersede_memory(self, old_id, new_id):
        if old_id == new_id:
            raise ValidazioneError("La voce che sostituisce deve essere diversa.")
        self._ex(self._t("memory").update({"superseded_by": new_id}, returning=self._minimal()).eq("id", old_id))

    # --- piani (Guardian Intelligence) --------------------------------------------
    def create_plan(self, goal, piano, project_id=None, provider=None, model=None, created_by=None):
        r = self._ex(self._t("plans").insert({"goal": pulisci(goal, 1000, True, "obiettivo"), "piano": piano,
                                              "project_id": project_id, "provider": provider, "model": model,
                                              "created_by": created_by}))[0]
        self.add_event("plan_created", f"Piano proposto ({len(piano.get('tasks', []))} task): {goal[:200]}",
                       user_id=created_by, project_id=project_id)
        return r["id"]

    def plans(self, stato=None, limit=30):
        q = self._t("plans").select("*")
        if stato:
            q = q.eq("stato", stato)
        return self._ex(q.order("created_at", desc=True).limit(limit))

    def plan(self, plan_id):
        r = self._ex(self._t("plans").select("*").eq("id", plan_id))
        return r[0] if r else None

    def set_plan_state(self, plan_id, stato, by=None):
        stato = scegli(stato, STATI_PIANO, "Stato piano")
        self._ex(self._t("plans").update({"stato": stato}, returning=self._minimal()).eq("id", plan_id))
        self.add_event(f"plan_{'confirmed' if stato == 'confermato' else 'discarded'}", f"Piano #{plan_id}: {stato}",
                       user_id=by)

    # --- approvazioni ---------------------------------------------------------------
    def approvals(self, status=None):
        q = self._t("approvals").select("*")
        if status:
            q = q.eq("status", status)
        return self._ex(q.order("created_at", desc=True))

    def request_approval(self, action, description="", task_id=None, requested_by=None, action_type="altro",
                         reason=None, impact=None, data_involved=None, agent_id=None):
        r = self._ex(self._t("approvals").insert({
            "task_id": task_id, "action": pulisci(action, 200, True, "azione"),
            "description": pulisci(description, 2000), "requested_by": requested_by,
            "action_type": scegli(action_type, ACTION_TYPES, "Tipo di azione"),
            "reason": pulisci(reason, 1000, nome="motivo") or None, "impact": pulisci(impact, 1000, nome="impatto") or None,
            "data_involved": pulisci(data_involved, 1000, nome="dati coinvolti") or None, "agent_id": agent_id}))[0]
        self.add_event("approval_requested", f"Richiesta approvazione: {action}", user_id=requested_by,
                       task_id=task_id, agent_id=agent_id, severity="warning")
        return r["id"]

    def decide_approval(self, approval_id, status, decided_by):
        status = scegli(status, APPROVAL_STATI[1:], "Decisione")
        r = self._ex(self._t("approvals").update({"status": status, "decided_by": decided_by, "decided_at": adesso()})
                     .eq("id", approval_id).eq("status", "richiesta"))
        if r:
            self.add_event("approval_decided", f"Approvazione #{approval_id} ({r[0]['action']}): {status}",
                           user_id=decided_by, task_id=r[0].get("task_id"))
