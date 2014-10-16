all: server

%.o: %.c
	${CC} -c ${CFLAGS} ${CPPFLAGS} -o $@ $<

clean:
	-rm -rf *.o server
