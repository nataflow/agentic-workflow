"""29 S2 — klien MCP `nataflow_client.py`: sesi Streamable HTTP, bearer, JSON/SSE, galat, dan sensor key."""
import pytest

from conftest import PLUGINS, load_module
from nataflow_fake import KEY, FakeMCP, ToolError

COPIES = [PLUGINS / p / "skills/_common/nataflow_client.py" for p in ("analyst", "backend", "frontend", "quickdev")] + [
    PLUGINS / "nataflow/skills/create-artifact/scripts/nataflow_client.py"]


@pytest.fixture(scope="module")
def nc():
    return load_module(COPIES[1], "nataflow_client_29")


@pytest.mark.regression("29 S2")
def test_salinan_identik_di_kelima_lokasi():
    assert len({p.read_bytes() for p in COPIES}) == 1, "salinan nataflow_client.py berbeda"


def test_pustaka_bukan_cli():
    assert "__main__" not in COPIES[1].read_text(encoding="utf-8")


@pytest.mark.parametrize("sse", [False, True], ids=["json", "sse"])
def test_sesi_bearer_dan_tool(nc, sse):
    with FakeMCP(sse=sse) as fake:
        fake.tools["echo"] = lambda a: {"got": a}
        with nc.Session(fake.url, KEY) as s:
            assert s.call_json("echo", {"x": 1}) == {"got": {"x": 1}}
            sid = s.session_id
        assert sid and sid not in fake.sessions, "sesi ditutup (DELETE) sesudah with"
    methods = [r["body"].get("method") for r in fake.requests]
    assert methods == ["initialize", "notifications/initialized", "tools/call"]
    assert all(r["headers"]["Authorization"] == "Bearer " + KEY for r in fake.requests)
    assert "Mcp-Session-Id" not in fake.requests[0]["headers"]
    assert fake.requests[2]["headers"]["Mcp-Session-Id"] == sid


def test_is_error_menjadi_galat_tool(nc):
    with FakeMCP() as fake:
        def boom(_a):
            raise ToolError("task not found")
        fake.tools["boom"] = boom
        with nc.Session(fake.url, KEY) as s, pytest.raises(nc.NataflowError) as exc:
            s.call("boom", {})
    assert exc.value.kind == "tool" and exc.value.message == "boom: task not found"


def test_galat_json_rpc_menjadi_galat_tool(nc):
    with FakeMCP() as fake, nc.Session(fake.url, KEY) as s, pytest.raises(nc.NataflowError) as exc:
        s.call("tidak_ada", {})
    assert exc.value.kind == "tool" and "not found" in exc.value.message


def test_key_ditolak_tanpa_membocorkan_key(nc):
    salah = "nfk_salah_sekali_987"
    with FakeMCP() as fake, pytest.raises(nc.NataflowError) as exc:
        nc.Session(fake.url, salah).open()
    assert exc.value.kind == "transport" and "HTTP 401" in exc.value.message and salah not in exc.value.message


def test_http_galat_lain_dikutip_dan_disensor(nc):
    with FakeMCP() as fake:
        fake.status_override = 500
        with pytest.raises(nc.NataflowError) as exc:
            nc.Session(fake.url, KEY).open()
    assert "HTTP 500" in exc.value.message and KEY not in exc.value.message


def test_server_tidak_terjangkau(nc):
    with pytest.raises(nc.NataflowError) as exc:
        nc.Session("http://127.0.0.1:9/mcp", KEY, timeout=5).open()
    assert exc.value.kind == "transport" and "tidak dapat menghubungi" in exc.value.message


def test_sesi_kedaluwarsa_baca_diulang_sekali(nc):
    with FakeMCP() as fake:
        fake.tools["list_task"] = lambda a: []
        with nc.Session(fake.url, KEY) as s:
            fake.expire_next = True
            assert s.call_json("list_task", {}, read=True) == []
    assert [r["body"].get("method") for r in fake.requests].count("initialize") == 2


def test_sesi_kedaluwarsa_tulis_tidak_diulang(nc):
    with FakeMCP() as fake:
        fake.tools["create_task"] = lambda a: {"id": "x"}
        with nc.Session(fake.url, KEY) as s:
            fake.expire_next = True
            with pytest.raises(nc.NataflowError) as exc:
                s.call("create_task", {})
    assert "tidak diulang otomatis" in exc.value.message and fake.calls == []


def test_balikan_bukan_json(nc):
    with FakeMCP() as fake:
        fake.tools["teks"] = lambda a: "bukan json"
        with nc.Session(fake.url, KEY) as s, pytest.raises(nc.NataflowError) as exc:
            s.call_json("teks", {})
    assert "bukan JSON" in exc.value.message


def test_as_list(nc):
    assert nc.as_list([1]) == [1]
    assert nc.as_list({"data": [2]}, "data") == [2]
    with pytest.raises(nc.NataflowError):
        nc.as_list({"x": 1}, "data")
