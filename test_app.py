import runpy

def test_app_prints_title(capsys):
	runypy.run_path("app.py")
	assert "Coporate Security Application" in capsys.readouterr().out

