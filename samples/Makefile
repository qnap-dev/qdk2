.PHONY: all clean

all:
	@for i in $$(ls -d */); do \
		i=$${i%%/}; \
		tar zcf $$i.tar.gz $$i; \
	done

clean:
	@rm -f *.tar.gz
