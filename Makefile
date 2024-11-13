run:
	python main.py

test:
	pytest -s

test_run:
	(python utils/testUtils.py & sleep 2) && python main.py

run_nodes:
	export PROTOCOL_BUFFERS_PYTHON_IMPLEMENTATION=python
	python utils/testUtils.py