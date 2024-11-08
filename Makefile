run:
	python main.py

test:
	pytest -s

test_run:
	(python utils/testUtils.py & sleep 3) && python main.py

run_nodes:
	python utils/testUtils.py