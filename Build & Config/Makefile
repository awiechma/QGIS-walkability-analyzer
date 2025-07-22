#/***************************************************************************
# WalkabilityAnalyzer
#
# Walkability assessment for urban areas
#							 -------------------
#		begin				: 2025-07-18
#		git sha				: $Format:%H$
#		copyright			: (C) 2025 by Amon Wiechmann
#		email				: awiechma@uni-muenster.de
# ***************************************************************************/
#
#/***************************************************************************
# *																		 *
# *   This program is free software; you can redistribute it and/or modify  *
# *   it under the terms of the GNU General Public License as published by  *
# *   the Free Software Foundation; either version 2 of the License, or	 *
# *   (at your option) any later version.								   *
# *																		 *
# ***************************************************************************/

#################################################
# Edit the following to match your sources lists
#################################################

#Add iso code for any locales you want to support here (space separated)
# default is no locales
# LOCALES = af
LOCALES =

# If locales are enabled, set the name of the lrelease binary on your system
#LRELEASE = lrelease
#LRELEASE = lrelease-qt4

# Plugin name
PLUGINNAME = walkability_analyzer

# All Python source files
SOURCES = \
	__init__.py \
	walkability_analyzer.py \
	walkability_analyzer_dialog.py \
	config.py \
	walkability_engine.py \
	ors_client.py \
	overpass_client.py \
	pdf_exporter.py \
	dependency_checker.py

# Python files to deploy
PY_FILES = \
	__init__.py \
	walkability_analyzer.py \
	walkability_analyzer_dialog.py \
	config.py \
	walkability_engine.py \
	ors_client.py \
	overpass_client.py \
	pdf_exporter.py \
	dependency_checker.py

# UI files
UI_FILES = walkability_analyzer_dialog_base.ui

# Extra files
EXTRAS = metadata.txt icon.png requirements.txt

# Extra directories
EXTRA_DIRS =

# Compiled resource files
COMPILED_RESOURCE_FILES = resources.py

# PEP8 exclusions
PEP8EXCLUDE=pydev,resources.py,conf.py,third_party,ui

# QGIS installation directory
# Adjust this path according to your system:
# Linux: ~/.local/share/QGIS/QGIS3/profiles/default/python/plugins/
# Mac: ~/Library/Application Support/QGIS/QGIS3/profiles/default/python/plugins/
# Windows: AppData\Roaming\QGIS\QGIS3\profiles\default\python\plugins
QGISDIR=C:\Users\ajwie\AppData/Roaming/QGIS/QGIS3/profiles/default/python/plugins

#################################################
# Normally you would not need to edit below here
#################################################

HELP = help/build/html
PLUGIN_UPLOAD = $(c)/plugin_upload.py
RESOURCE_SRC=$(shell grep '^ *<file' resources.qrc | sed 's@</file>@@g;s/.*>//g' | tr '\n' ' ')

.PHONY: default
default:
	@echo "Walkability Analyzer Plugin Build System"
	@echo "========================================"
	@echo ""
	@echo "Available targets:"
	@echo "  compile    - Compile resources and UI files"
	@echo "  deploy     - Deploy plugin to QGIS directory"
	@echo "  zip        - Create zip package for distribution"
	@echo "  clean      - Clean compiled files"
	@echo "  test       - Run tests"
	@echo "  pep8       - Check PEP8 compliance"
	@echo "  pylint     - Run pylint"
	@echo ""
	@echo "For automated plugin management, consider using pb_tool:"
	@echo "  pip install pb_tool"
	@echo "  pb_tool deploy"

compile: $(COMPILED_RESOURCE_FILES)

%.py : %.qrc $(RESOURCES_SRC)
	pyrcc5 -o $*.py  $<

%.qm : %.ts
	$(LRELEASE) $<

test: compile transcompile
	@echo
	@echo "=========================="
	@echo "Running Walkability Tests"
	@echo "=========================="
	@echo
	@-export PYTHONPATH=`pwd`:$(PYTHONPATH); \
		export QGIS_DEBUG=0; \
		export QGIS_LOG_FILE=/dev/null; \
		python -m pytest test/ -v || true
	@echo "=========================="

deploy: compile doc transcompile
	@echo
	@echo "================================================"
	@echo "Deploying Walkability Analyzer to QGIS directory"
	@echo "================================================"
	# Create plugin directory
	mkdir -p $(HOME)/$(QGISDIR)/$(PLUGINNAME)
	
	# Copy Python files
	cp -vf $(PY_FILES) $(HOME)/$(QGISDIR)/$(PLUGINNAME)/
	
	# Copy UI files
	cp -vf $(UI_FILES) $(HOME)/$(QGISDIR)/$(PLUGINNAME)/
	
	# Copy resources
	cp -vf $(COMPILED_RESOURCE_FILES) $(HOME)/$(QGISDIR)/$(PLUGINNAME)/
	
	# Copy extras
	cp -vf $(EXTRAS) $(HOME)/$(QGISDIR)/$(PLUGINNAME)/
	
	# Copy translations
	@if [ -d i18n ]; then \
		cp -vfr i18n $(HOME)/$(QGISDIR)/$(PLUGINNAME)/; \
	fi
	
	# Copy help
	@if [ -d $(HELP) ]; then \
		cp -vfr $(HELP) $(HOME)/$(QGISDIR)/$(PLUGINNAME)/help; \
	fi
	
	# Copy extra directories
	@for EXTRA_DIR in $(EXTRA_DIRS); do \
		if [ -d $$EXTRA_DIR ]; then \
			cp -vfr $$EXTRA_DIR $(HOME)/$(QGISDIR)/$(PLUGINNAME)/; \
		fi; \
	done
	
	@echo
	@echo "✅ Plugin successfully deployed to:"
	@echo "   $(HOME)/$(QGISDIR)/$(PLUGINNAME)/"
	@echo
	@echo "💡 Next steps:"
	@echo "   1. Restart QGIS"
	@echo "   2. Enable plugin in Plugin Manager"
	@echo "   3. Install dependencies: pip install -r requirements.txt"

# Clean compiled files
dclean:
	@echo
	@echo "==============================="
	@echo "Cleaning compiled Python files"
	@echo "==============================="
	find $(HOME)/$(QGISDIR)/$(PLUGINNAME) -iname "*.pyc" -delete 2>/dev/null || true
	find $(HOME)/$(QGISDIR)/$(PLUGINNAME) -iname ".git" -prune -exec rm -Rf {} \; 2>/dev/null || true

# Remove deployed plugin
derase:
	@echo
	@echo "=========================="
	@echo "Removing deployed plugin"
	@echo "=========================="
	rm -Rf $(HOME)/$(QGISDIR)/$(PLUGINNAME)
	@echo "✅ Plugin removed from QGIS directory"

# Create distribution zip
zip: deploy dclean
	@echo
	@echo "=============================="
	@echo "Creating distribution package"
	@echo "=============================="
	rm -f $(PLUGINNAME).zip
	cd $(HOME)/$(QGISDIR); zip -9r $(CURDIR)/$(PLUGINNAME).zip $(PLUGINNAME)
	@echo "✅ Created: $(PLUGINNAME).zip"

# Create git package
package: compile
	@echo
	@echo "=========================="
	@echo "Creating git-based package"
	@echo "=========================="
	@if [ -z "$(VERSION)" ]; then \
		echo "❌ VERSION not specified. Usage: make package VERSION=v1.0.0"; \
		exit 1; \
	fi
	rm -f $(PLUGINNAME).zip
	git archive --prefix=$(PLUGINNAME)/ -o $(PLUGINNAME).zip $(VERSION)
	@echo "✅ Created: $(PLUGINNAME).zip (from $(VERSION))"

# Upload to plugin repository
upload: zip
	@echo
	@echo "==============================="
	@echo "Uploading to QGIS Plugin repo"
	@echo "==============================="
	$(PLUGIN_UPLOAD) $(PLUGINNAME).zip

# Translation support
transup:
	@echo "Updating translation files..."
	@chmod +x scripts/update-strings.sh
	@scripts/update-strings.sh $(LOCALES)

transcompile:
	@echo "Compiling translation files..."
	@chmod +x scripts/compile-strings.sh
	@scripts/compile-strings.sh $(LRELEASE) $(LOCALES)

transclean:
	@echo "Cleaning translation files..."
	rm -f i18n/*.qm

# Clean all generated files
clean:
	@echo "Cleaning generated files..."
	@if [ -n "$(COMPILED_RESOURCE_FILES)" ]; then \
		rm -f $(COMPILED_RESOURCE_FILES); \
	fi
	@echo "✅ Cleaned compiled files"

# Build documentation
doc:
	@echo "Building documentation..."
	@if [ -d help ]; then \
		cd help && make html; \
	fi

# Run pylint
pylint:
	@echo
	@echo "=================="
	@echo "Running PyLint"
	@echo "=================="
	@pylint --reports=n --rcfile=pylintrc . || true
	@echo
	@echo "💡 To fix QGIS import errors, source the environment first:"
	@echo "   source scripts/run-env-linux.sh <path-to-qgis>"
	@echo "   make pylint"

# Run PEP8 style checking
pep8:
	@echo
	@echo "=================="
	@echo "Running PEP8 check"
	@echo "=================="
	@pep8 --repeat --ignore=E203,E121,E122,E123,E124,E125,E126,E127,E128 \
		--exclude $(PEP8EXCLUDE) . || true
	@echo
	@echo "Excluded from check: $(PEP8EXCLUDE)"

# Check dependencies
deps:
	@echo "Checking Python dependencies..."
	@python -c "
import sys
required = ['requests', 'shapely', 'reportlab', 'pyproj']
missing = []
for pkg in required:
    try:
        __import__(pkg)
        print(f'✅ {pkg}')
    except ImportError:
        missing.append(pkg)
        print(f'❌ {pkg}')
if missing:
    print(f'\n💡 Install missing packages: pip install {\" \".join(missing)}')
    sys.exit(1)
else:
    print('\n🎉 All dependencies satisfied!')
"

# Show help
help:
	@echo "Walkability Analyzer Plugin Build System"
	@echo "========================================"
	@echo ""
	@echo "Common commands:"
	@echo "  make deploy    - Deploy plugin to QGIS"
	@echo "  make zip       - Create distribution package"  
	@echo "  make deps      - Check Python dependencies"
	@echo "  make test      - Run plugin tests"
	@echo "  make clean     - Clean generated files"
	@echo ""
	@echo "Development commands:"
	@echo "  make pep8      - Check code style"
	@echo "  make pylint    - Run code analysis"
	@echo "  make doc       - Build documentation"
	@echo ""
	@echo "Plugin files:"
	@echo "  Python: $(PY_FILES)"
	@echo "  UI:     $(UI_FILES)"
	@echo "  Extras: $(EXTRAS)"