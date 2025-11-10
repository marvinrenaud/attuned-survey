.PHONY: activities-rebaseline activities-test activities-rollback reports-dir help

# Python from venv (relative to backend directory)
PYTHON := venv/bin/python

# Default target
help:
	@echo "Attuned Activity Rebaseline - Available Targets"
	@echo "================================================"
	@echo ""
	@echo "  make activities-rebaseline   Run full rebaseline (migrations, import, enrichment)"
	@echo "  make activities-test         Run test suite"
	@echo "  make activities-rollback     Rollback migrations (WARNING: data loss)"
	@echo "  make reports-dir             Create reports directory"
	@echo "  make help                    Show this help message"
	@echo ""

# Create reports directory
reports-dir:
	@mkdir -p reports

# Full rebaseline workflow
activities-rebaseline: reports-dir
	@echo "========================================================================"
	@echo "Attuned Activity Rebaseline - Full Workflow"
	@echo "========================================================================"
	@echo ""
	@echo "==> Step 1: Running database migrations..."
	cd backend && $(PYTHON) scripts/run_migrations.py --apply
	@echo ""
	@echo "==> Step 2: Migrating boundary taxonomy..."
	cd backend && $(PYTHON) scripts/migrate_boundary_taxonomy.py --apply
	@echo ""
	@echo "==> Step 3: Importing activities from XLSX..."
	cd backend && $(PYTHON) scripts/import_activities.py \
		--xlsx "../Consolidated_ToD_Activities (20).xlsx" \
		--sheet "Consolidated Activities" \
		--apply | tee ../reports/import_summary.txt
	@echo ""
	@echo "==> Step 4: Validating database schema and data..."
	cd backend && $(PYTHON) scripts/verify_schema.py | tee ../reports/validation_report.txt
	@echo ""
	@echo "==> Step 5: Running diagnostics..."
	cd backend && $(PYTHON) scripts/run_diagnostics.py | tee ../reports/diagnostics.txt
	@echo ""
	@echo "========================================================================"
	@echo "✅ Rebaseline complete! Check reports/ directory for details."
	@echo "========================================================================"

# Test suite
activities-test:
	@echo "========================================================================"
	@echo "Running Activity Test Suite"
	@echo "========================================================================"
	@echo ""
	@echo "==> Testing migration dry-run..."
	cd backend && $(PYTHON) scripts/run_migrations.py --dry-run
	@echo ""
	@echo "==> Testing import dry-run..."
	cd backend && $(PYTHON) scripts/import_activities.py \
		--xlsx "../Consolidated_ToD_Activities (20).xlsx" \
		--sheet "Consolidated Activities" \
		--dry-run
	@echo ""
	@echo "==> Testing boundary migration dry-run..."
	cd backend && $(PYTHON) scripts/migrate_boundary_taxonomy.py --dry-run
	@echo ""
	@echo "========================================================================"
	@echo "✅ All tests completed!"
	@echo "========================================================================"

# Rollback (with confirmation)
activities-rollback:
	@echo "========================================================================"
	@echo "⚠️  WARNING: This will rollback migrations and result in data loss!"
	@echo "========================================================================"
	@echo ""
	@echo "Press Ctrl+C to cancel, or Enter to continue..."
	@read confirm
	cd backend && $(PYTHON) scripts/run_migrations.py --rollback --apply
	@echo ""
	@echo "✅ Rollback complete"

