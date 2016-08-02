LANG_PATH=i18n
LANG_SOURCES=$(wildcard $(LANG_PATH)/*.ts)
LANG_FILES=$(patsubst $(LANG_PATH)/%.ts, $(LANG_PATH)/%.qm, $(LANG_SOURCES))

PRO_PATH=.
PRO_FILES=$(wildcard $(PRO_PATH)/*.pro)

ALL_FILES= ${LANG_FILES}

all: $(ALL_FILES)

ts: $(PRO_FILES)
	pylupdate4 -verbose $<

lang: $(LANG_FILES)

$(LANG_FILES): $(LANG_PATH)/%.qm: $(LANG_PATH)/%.ts
	lrelease $<

pep8:
	@echo
	@echo "-----------"
	@echo "PEP8 issues"
	@echo "-----------"
	@pep8 --repeat --ignore=E203,E121,E122,E123,E124,E125,E126,E127,E128 . || true

clean:
	rm -f $(ALL_FILES)
	find -name "*.pyc" -exec rm -f {} \;
	rm -f *.zip

package: clean ts all
	cd .. && rm -f *.zip && zip -r photo2shape.zip photo2shape -x \*.pyc \*.ts \*.pro \*~ \*.git\* \*Makefile*
	mv ../photo2shape.zip .

upload: package
	plugin_uploader.py photo2shape.zip
