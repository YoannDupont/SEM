MODELS = resources/models/fr/chunk/mwe_all resources/models/fr/chunk/mwe_np resources/models/fr/chunk/plain_all resources/models/fr/chunk/plain_np resources/models/fr/NER/plain_NER resources/models/fr/POS/mwe.lefff resources/models/fr/POS/mwe  resources/models/fr/POS/plain.lefff resources/models/fr/POS/plain

all: ext/wapiti/wapiti $(MODELS)

ext/wapiti:
	@echo "Unpacking $@.tar.gz"
	cd $(@D) ; tar -xf $(@F).tar.gz

ext/wapiti/wapiti: ext/wapiti
	@echo "Building wapiti"
	cd ext/wapiti ; $(MAKE) $(MFLAGS)

models: $(MODELS)

$(MODELS):
	@echo "Unpacking $@"
	cd $(@D) ; tar -xf $(@F).tar.gz


.PHONY : clean
clean:
	@echo "Cleaning up"
	rm -r ext/wapiti $(MODELS)
