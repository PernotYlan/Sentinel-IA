#!/usr/bin/env python3
"""
Sentinel-IA — Interface d'administration
Lance avec : python3 tui.py
"""

from textual.app import App, ComposeResult
from textual.widgets import Header, Footer, Static, RichLog, ListView, ListItem, Label, Input, DataTable
from textual.containers import Horizontal, Vertical
from textual.screen import ModalScreen
from textual.reactive import reactive
from textual import work
from rich.text import Text
from collections import deque
from src.env import check_for_environment
from src.redis import connect_redis
from src.db import init_db, store_event, dump_sqlite, get_anomalies, get_events
from src.logger import add_tui_handler, remove_tui_handler
import logging
import json
import asyncio
import time
import psutil
import os
from datetime import datetime

VERSION = "v1.1"


class DetachPopup(ModalScreen):
    """Popup explicatif pour le detachement tmux"""

    BINDINGS = [("escape", "dismiss", "Fermer")]

    def compose(self) -> ComposeResult:
        yield Static(
            "\n"
            " [bold]Detachement — tmux[/bold]\n\n"
            " Textual ne supporte pas le detachement natif.\n"
            " Utilise [cyan]tmux[/cyan] pour lancer et detacher le TUI :\n\n"
            "   [green]tmux new -s sentinel[/green]       creer une session\n"
            "   [green]python3 tui.py[/green]             lancer le TUI\n"
            "   [yellow]Ctrl+B  puis  D[/yellow]            detacher\n"
            "   [green]tmux attach -t sentinel[/green]    reattacher\n\n"
            " Installation : [cyan]apt install tmux[/cyan]\n\n"
            " [dim]Appuie sur Echap pour fermer[/dim]\n",
            id="popup_content"
        )

    DEFAULT_CSS = """
    DetachPopup {
        align: center middle;
    }
    #popup_content {
        width: 52;
        height: 18;
        border: solid yellow;
        background: $surface;
        padding: 0 1;
    }
    """


class _MLContent(Static):
    """Contenu du popup ML rendu via Rich Text"""

    def render(self) -> Text:
        import src.model_if as _model_if
        import src.model_ae as _model_ae
        from datetime import datetime as _dt

        def _mtime(path: str) -> str:
            return _dt.fromtimestamp(os.path.getmtime(path)).strftime("%d/%m/%Y") if os.path.exists(path) else "--/--/----"

        if_status = "charge" if _model_if.loaded_from_disk else ("entraine" if _model_if.trained else "non entraine")
        if_color  = "green" if (_model_if.loaded_from_disk or _model_if.trained) else "red"

        ae_status = "charge" if _model_ae.model is not None else "non entraine"
        ae_color  = "green" if _model_ae.model is not None else "red"
        ae_threshold = f"{_model_ae.threshold:.6f}" if _model_ae.threshold is not None else "--"

        t = Text()
        t.append("Statut des modeles ML\n", style="bold magenta")
        t.append("Statut, derniere date d'entrainement et configuration de chaque modele\n\n", style="dim")

        t.append("Isolation Forest\n", style="bold green")
        t.append("  Statut        ", style="dim")
        t.append(f"{if_status}\n", style=if_color)
        t.append("  Dernier entr. ", style="dim")
        t.append(f"{_mtime(_model_if.MODEL_PATH)}\n", style="white")
        t.append("  contamination ", style="dim")
        t.append(f"{_model_if._contamination:.4f} / 1.0\n\n", style="cyan")

        t.append("XGBoost\n", style="bold yellow")
        t.append("  Statut        ", style="dim")
        t.append("pre-entraine\n", style="yellow")
        t.append("  Dataset       ", style="dim")
        t.append("NSL-KDD + CICIDS2017\n\n", style="white")

        t.append("Autoencoder\n", style="bold blue")
        t.append("  Statut        ", style="dim")
        t.append(f"{ae_status}\n", style=ae_color)
        t.append("  Dernier entr. ", style="dim")
        t.append(f"{_mtime(_model_ae.MODEL_PATH)}\n", style="white")
        t.append("  Seuil         ", style="dim")
        t.append(f"{ae_threshold}\n", style="cyan")
        return t


class AnomaliesPopup(ModalScreen):
    """Popup listant les anomalies detectees dans SQLite"""

    BINDINGS = [("escape", "dismiss", "Fermer")]

    DEFAULT_CSS = """
    AnomaliesPopup { align: center middle; }
    #anomalies_box {
        width: 80; height: 24;
        border: solid red;
        background: $surface;
        padding: 1 2;
    }
    """

    def compose(self) -> ComposeResult:
        with Vertical(id="anomalies_box"):
            yield Label("[bold red]Anomalies detectees[/bold red]", markup=True)
            yield Label("[dim]Montre les anomalies confirmees retrouvees dans buffer.db[/dim]\n", markup=True)
            table = DataTable()
            table.add_columns("Timestamp", "Source IP", "Modele", "Score")
            rows = get_anomalies(50)
            table.add_rows(rows if rows else [("--:--:--", "-", "-", "-")])
            yield table
            yield Label("\n[dim]Echap pour fermer[/dim]", markup=True)


class DBPopup(ModalScreen):
    """Popup de navigation libre dans buffer.db"""

    BINDINGS = [("escape", "dismiss", "Fermer")]

    DEFAULT_CSS = """
    DBPopup { align: center middle; }
    #db_box {
        width: 80; height: 24;
        border: solid blue;
        background: $surface;
        padding: 1 2;
    }
    """

    def compose(self) -> ComposeResult:
        with Vertical(id="db_box"):
            yield Label("[bold blue]Base de donnees — buffer.db[/bold blue]", markup=True)
            yield Label("[dim]Browse la base de donnees librement en direct[/dim]\n", markup=True)
            table = DataTable()
            table.add_columns("ID", "Source", "Timestamp", "Apercu")
            raw_rows = get_events(50)
            if raw_rows:
                formatted = [
                    (str(r[0]), r[1], r[2], json.loads(r[3]).get("src_ip", r[3][:30]) if r[1] == "zeek" else r[3][:30])
                    for r in raw_rows
                ]
            else:
                formatted = [("-", "-", "-", "-")]
            table.add_rows(formatted)
            yield table
            yield Label("\n[dim]Echap pour fermer[/dim]", markup=True)


class MLPopup(ModalScreen):
    """Popup de statut des modeles ML"""

    BINDINGS = [("escape", "dismiss", "Fermer")]

    DEFAULT_CSS = """
    MLPopup { align: center middle; }
    #ml_box {
        width: 64; height: 24;
        border: solid magenta;
        background: $surface;
        padding: 1 2;
    }
    """

    def compose(self) -> ComposeResult:
        with Vertical(id="ml_box"):
            yield _MLContent()
            yield Label("[dim]Echap pour fermer[/dim]", markup=True)


class ConfigPopup(ModalScreen):
    """Popup de modification des variables d'environnement"""

    BINDINGS = [("escape", "dismiss", "Fermer")]

    DEFAULT_CSS = """
    ConfigPopup { align: center middle; }
    #config_box {
        width: 60; height: 24;
        border: solid yellow;
        background: $surface;
        padding: 1 2;
    }
    Input {
        margin: 0 0 1 0;
    }
    """

    ENV_VARS = ["REDIS_HOST", "REDIS_PORT", "CONTAMINATION", "TRAIN_THRESHOLD"]

    def compose(self) -> ComposeResult:
        with Vertical(id="config_box"):
            yield Label("[bold yellow]Configuration — .env[/bold yellow]", markup=True)
            yield Label("[dim]Modifie les variables d'environnement sans afficher leurs valeurs actuelles.\nLaisse vide pour conserver la valeur existante.[/dim]\n", markup=True)
            for var in self.ENV_VARS:
                yield Label(var, markup=False)
                yield Input(placeholder="nouvelle valeur...", id=f"input_{var}")
            yield Label("\n[dim]Echap pour fermer[/dim]", markup=True)


class TUILogHandler(logging.Handler):
    """Handler logging qui redirige les entrees vers le RichLog du TUI"""

    def __init__(self, log_widget: RichLog):
        super().__init__()
        self._log = log_widget

    def emit(self, record: logging.LogRecord):
        msg = self.format(record)
        level = record.levelname
        if level == "WARNING":
            color = "yellow"
        elif level == "ERROR" or level == "CRITICAL":
            color = "red"
        elif level == "DEBUG":
            color = "dim"
        else:
            color = "white"
        try:
            self._log.write(f"[{color}]{msg}[/{color}]")
        except Exception:
            pass


class AppHeader(Static):
    """Barre d'information en haut de l'ecran"""

    simulating: reactive[bool] = reactive(False)

    def render(self) -> Text:
        now = datetime.now().strftime("%d/%m/%Y  %H:%M:%S")
        t = Text()
        t.append("Sentinel-IA\n", style="bold white")
        t.append(f"{VERSION}\n\n", style="cyan")
        t.append("Client   ", style="dim")
        t.append("clientA\n", style="bold yellow")
        t.append("Statut   ", style="dim")
        t.append("en ligne\n", style="green bold")
        t.append("Mode     ", style="dim")
        if self.simulating:
            t.append("SIMULATION\n", style="bold red on yellow")
        else:
            t.append("surveillance\n", style="white")
        t.append("\n")
        t.append(now, style="dim")
        return t


class EnvStatus(Static):
    """Panneau d'etat de l'environnement systeme"""

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        net = psutil.net_io_counters()
        self._last_bytes_sent = net.bytes_sent
        self._last_bytes_recv = net.bytes_recv
        self._last_time = time.time()
        self._tx_mbps: float = 0.0
        self._rx_mbps: float = 0.0

    def _update_net(self):
        now = time.time()
        net = psutil.net_io_counters()
        elapsed = now - self._last_time or 1
        self._tx_mbps = (net.bytes_sent - self._last_bytes_sent) / elapsed / 1024 / 1024
        self._rx_mbps = (net.bytes_recv - self._last_bytes_recv) / elapsed / 1024 / 1024
        self._last_bytes_sent = net.bytes_sent
        self._last_bytes_recv = net.bytes_recv
        self._last_time = now

    def _bar(self, t: Text, label: str, percent: float, color: str):
        filled = int(percent / 10)
        bar = "█" * filled + "░" * (10 - filled)
        t.append(f"{label:<5}", style="bold")
        t.append(f" [{bar}] ", style=color)
        t.append(f"{percent:>4.0f}%\n")

    def render(self) -> Text:
        self._update_net()
        cpu  = psutil.cpu_percent()
        ram  = psutil.virtual_memory().percent
        disk = psutil.disk_usage("/").percent

        t = Text()
        t.append("Env Status\n", style="bold")
        t.append("clientA\n\n", style="cyan bold")
        self._bar(t, "CPU",  cpu,  "red" if cpu  > 80 else "green")
        self._bar(t, "RAM",  ram,  "red" if ram  > 80 else "blue")
        self._bar(t, "Disk", disk, "red" if disk > 80 else "yellow")
        t.append("\n")
        t.append("Net TX  ", style="bold")
        t.append(f"{self._tx_mbps:>6.2f} MB/s\n", style="green")
        t.append("Net RX  ", style="bold")
        t.append(f"{self._rx_mbps:>6.2f} MB/s\n", style="blue")
        return t


class Counters(Static):
    """Panneau de compteurs d'evenements - affiche le debit en ev/min"""

    zeek_rate: reactive[float] = reactive(0.0)
    syslog_rate: reactive[float] = reactive(0.0)
    db_rate: reactive[float] = reactive(0.0)

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self._zeek_ts: deque = deque()
        self._syslog_ts: deque = deque()
        self._db_ts: deque = deque()

    def _rate(self, ts_deque: deque) -> float:
        now = time.time()
        cutoff = now - 60
        while ts_deque and ts_deque[0] < cutoff:
            ts_deque.popleft()
        return float(len(ts_deque))

    def record(self, source: str):
        now = time.time()
        if source == "zeek":
            self._zeek_ts.append(now)
            self.zeek_rate = self._rate(self._zeek_ts)
        elif source == "syslog":
            self._syslog_ts.append(now)
            self.syslog_rate = self._rate(self._syslog_ts)
        elif source == "db":
            self._db_ts.append(now)
            self.db_rate = self._rate(self._db_ts)

    def render(self) -> Text:
        t = Text()
        t.append("Evenements / min\n\n", style="bold")
        t.append("Zeek    ", style="green")
        t.append(f"{self.zeek_rate:>8.1f}\n")
        t.append("Syslog  ", style="blue")
        t.append(f"{self.syslog_rate:>8.1f}\n")
        t.append("Autres  ", style="yellow")
        t.append(f"{self.db_rate:>8.1f}\n")
        return t


class Travailleurs(Static):
    """Panneau d'etat des workers et de leurs files d'attente"""

    w1_queue: reactive[int] = reactive(0)
    w2_queue: reactive[int] = reactive(0)
    w3_queue: reactive[int] = reactive(0)
    w4_queue: reactive[int] = reactive(0)
    anomalies: reactive[int] = reactive(0)

    w1_online: reactive[bool] = reactive(True)
    w2_online: reactive[bool] = reactive(True)
    w3_online: reactive[bool] = reactive(True)
    w4_online: reactive[bool] = reactive(False)

    def _worker_line(self, t: Text, name: str, online: bool, queue: int):
        if online:
            t.append("● ", style="green")
            t.append(f"{name:<12}", style="bold")
            t.append("  queue: ")
            t.append(str(queue), style="cyan")
            t.append("\n")
        else:
            t.append("● ", style="red")
            t.append(f"{name:<12}", style="dim")
            t.append("  offline\n", style="dim")

    def render(self) -> Text:
        anomaly_str = "999+" if self.anomalies >= 1000 else str(self.anomalies)
        t = Text()
        t.append("Travailleurs\n\n", style="bold")
        self._worker_line(t, "Worker 1", self.w1_online, self.w1_queue)
        self._worker_line(t, "Worker 2", self.w2_online, self.w2_queue)
        self._worker_line(t, "Worker 3", self.w3_online, self.w3_queue)
        self._worker_line(t, "Worker 4", self.w4_online, self.w4_queue)
        t.append("\nAnomalies ", style="red bold")
        t.append(anomaly_str, style="red")
        return t


class SentinelTUI(App):
    CSS = """
    Screen {
        layout: vertical;
    }

    AppHeader {
        height: 14;
        background: $panel;
        padding: 1 2;
        border: solid $panel;
    }

    #body {
        height: 100%;
    }

    #sidebar {
        width: 40%;
        border-right: solid $panel;
    }

    ListView {
        background: $surface;
        align: center middle;
        content-align: center middle;
    }

    ListItem {
        padding: 1 2;
        width: 100%;
        content-align: center middle;
    }

    ListItem Label {
        width: 100%;
        text-align: center;
    }

    #main {
        width: 1fr;
        layout: vertical;
    }

    #top_row {
        height: 14;
    }

    EnvStatus {
        width: 38;
        height: 100%;
        border: solid green;
        padding: 1 2;
    }

    Counters {
        width: 26;
        height: 100%;
        border: solid blue;
        padding: 1 2;
    }

    Travailleurs {
        width: 1fr;
        height: 100%;
        border: solid magenta;
        padding: 1 2;
    }

    #log_panel {
        border: solid yellow;
        padding: 0 1;
        height: 1fr;
    }

    /* Flash rouge en mode simulation */
    .sim-flash EnvStatus      { border: solid red; }
    .sim-flash Counters       { border: solid red; }
    .sim-flash Travailleurs   { border: solid red; }
    .sim-flash #log_panel     { border: solid red; }
    .sim-flash #sidebar       { border-right: solid red; }
    """

    BINDINGS = [
        ("q", "quit", "Quitter"),
        ("m", "menu", "Menu"),
        ("d", "detach", "Detacher"),
    ]

    def compose(self) -> ComposeResult:
        with Horizontal(id="body"):
            with Vertical(id="sidebar"):
                yield AppHeader()
                yield ListView(
                    ListItem(Label("Dashboard"),    id="item_dashboard"),
                    ListItem(Label("Anomalies"),    id="item_anomalies"),
                    ListItem(Label("Base donnees"), id="item_db"),
                    ListItem(Label("Modeles ML"),   id="item_models"),
                    ListItem(Label("Configuration"),id="item_config"),
                    ListItem(Label("Simuler"),      id="item_simulate"),
                    ListItem(Label("Quitter"),      id="item_quit"),
                )
            with Vertical(id="main"):
                with Horizontal(id="top_row"):
                    yield EnvStatus()
                    yield Counters()
                    yield Travailleurs()
                yield RichLog(id="log_panel", highlight=True, markup=True)
        yield Footer()

    def on_mount(self):
        self.set_interval(2, self.query_one(EnvStatus).refresh)
        self.set_interval(1, self.query_one(AppHeader).refresh)
        init_db()
        self._tui_handler = TUILogHandler(self.query_one(RichLog))
        add_tui_handler(self._tui_handler)
        self._redis_loop()

    def on_unmount(self):
        if hasattr(self, "_tui_handler"):
            remove_tui_handler(self._tui_handler)

    def action_menu(self):
        pass

    def on_list_view_selected(self, event: ListView.Selected):
        item_id = event.item.id
        if item_id == "item_anomalies":
            self.push_screen(AnomaliesPopup())
        elif item_id == "item_db":
            self.push_screen(DBPopup())
        elif item_id == "item_models":
            self.push_screen(MLPopup())
        elif item_id == "item_config":
            self.push_screen(ConfigPopup())
        elif item_id == "item_simulate":
            self._toggle_simulate()
        elif item_id == "item_quit":
            self.exit()

    def action_detach(self):
        self.push_screen(DetachPopup())

    def _toggle_simulate(self):
        header = self.query_one(AppHeader)
        header.simulating = not header.simulating
        if header.simulating:
            self._flash_timer = self.set_interval(0.5, self._flash_borders)
            self._simulate()
        else:
            if hasattr(self, "_flash_timer"):
                self._flash_timer.stop()
            self.query_one("#body").remove_class("sim-flash")

    def _flash_borders(self):
        body = self.query_one("#body")
        if "sim-flash" in body.classes:
            body.remove_class("sim-flash")
        else:
            body.add_class("sim-flash")

    @work(exclusive=True, thread=True)
    def _simulate(self):
        """Simulation de donnees mockees — actif uniquement si Redis indisponible"""
        import random
        from src.logger import logger
        counters = self.query_one(Counters)
        workers = self.query_one(Travailleurs)
        sources = ["zeek", "zeek", "zeek", "syslog", "db"]
        header = self.query_one(AppHeader)

        while header.simulating:
            time.sleep(0.3)
            source = random.choice(sources)

            if source == "zeek":
                self.call_from_thread(counters.record, "zeek")
                self.call_from_thread(workers.__setattr__, "w1_queue", max(0, workers.w1_queue + random.randint(-1, 2)))
                logger.info(f"Zeek    192.168.1.{random.randint(1,254)} → 10.0.0.{random.randint(1,10)}  port {random.randint(1024,65535)}")
                if random.random() < 0.05:
                    self.call_from_thread(workers.__setattr__, "anomalies", workers.anomalies + 1)
                    logger.warning(f"ANOMALIE IF → XGB → AE  src=192.168.1.{random.randint(1,254)}")
            elif source == "syslog":
                self.call_from_thread(counters.record, "syslog")
                logger.info("Syslog  auth: session opened for user root")
            else:
                self.call_from_thread(counters.record, "db")
                logger.info("Autre   tags inconnus, dumpe dans SQLite")

    @work(thread=True)
    def _redis_loop(self):
        """Boucle Redis BLPOP dans un thread separe — met a jour le TUI via call_from_thread"""
        from src.logger import logger
        from src.model_if import run_isolation_forest, init_if
        import src.model_if as _model_if
        from src.model_xgb import run_xgb
        from src.model_ae import run_ae, init_ae

        init_if()
        init_ae()
        zeek_window = deque(maxlen=30000)

        r = connect_redis()
        counters = self.query_one(Counters)
        workers  = self.query_one(Travailleurs)

        while True:
            result = r.blpop(os.getenv("REDIS_KEY"), timeout=0)
            if not result:
                continue
            _, raw = result

            try:
                data = json.loads(raw)
            except Exception:
                logger.error("JSON invalide recu depuis Redis")
                continue

            tags = data.get("tags", [])

            if "zeek" in tags:
                parsed = {
                    "src_ip":    data.get("id.orig_h"),
                    "dst_ip":    data.get("id.resp_h"),
                    "src_port":  data.get("id.orig_p"),
                    "dst_port":  data.get("id.resp_p"),
                    "proto":     data.get("proto"),
                    "service":   data.get("service"),
                    "duration":  data.get("duration"),
                    "orig_bytes":data.get("orig_bytes"),
                    "resp_bytes":data.get("resp_bytes"),
                    "conn_state":data.get("conn_state"),
                    "orig_pkts": data.get("orig_pkts"),
                    "resp_pkts": data.get("resp_pkts"),
                    "timestamp": data.get("@timestamp"),
                }
                store_event("zeek", parsed)
                zeek_window.append(parsed)
                self.call_from_thread(counters.record, "zeek")
                logger.info(f"Zeek    {parsed['src_ip']} → {parsed['dst_ip']}  port {parsed['dst_port']}")

                if _model_if.loaded_from_disk or len(zeek_window) >= _model_if.TRAIN_THRESHOLD:
                    flagged = run_isolation_forest(zeek_window)
                    if flagged:
                        confirmed = max(run_xgb(flagged) or 0, run_ae(flagged) or 0)
                        if confirmed > 0:
                            self.call_from_thread(
                                workers.__setattr__, "anomalies", workers.anomalies + confirmed
                            )

            elif "beats_input_codec_plain_applied" in tags:
                dump_sqlite(data)
                self.call_from_thread(counters.record, "syslog")
                logger.info(f"Syslog  {data.get('message', '')[:60]}")

            else:
                dump_sqlite(data)
                self.call_from_thread(counters.record, "db")
                logger.debug(f"Autre   tags: {tags}")


if __name__ == "__main__":
    check_for_environment()
    SentinelTUI().run()
