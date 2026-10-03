# Convenience wrapper: forward commands issued from src/ to the repository
# Makefile, which owns the shared development and Docker targets.
.DEFAULT_GOAL := help

.PHONY: help
help:
	@$(MAKE) --no-print-directory -C .. help

%:
	@$(MAKE) --no-print-directory -C .. $@
