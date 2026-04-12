PYTHON ?= python

demo:
	$(PYTHON) src/run_analysis_environment.py demo

validate-demo:
	$(PYTHON) src/validate_inputs.py --input_dir data/demo

validate-actual:
	$(PYTHON) src/validate_inputs.py --input_dir data/actual_input

actual:
	$(PYTHON) src/run_analysis_environment.py actual --input_dir data/actual_input --output_dir data/output/actual_run
