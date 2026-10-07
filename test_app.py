import runpy

def test_app_prints_title(capsys):
	runpy.run_path("app.py")
	assert "Corporate Security Application" in capsys.readouterr().out

