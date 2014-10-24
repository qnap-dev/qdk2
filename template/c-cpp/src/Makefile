all: foobar daemon

foobar: libfoobar.so main.o
	${CC} -L. -Wall -o $@ $^ -lfoobar

libfoobar.so: foobar.o
	${CC} -shared -o $@ $^

foobar.o: foobar.c
	${CC} -c -Wall -Werror -fpic -o $@ $^

%.o: %.c
	${CC} -c ${CFLAGS} ${CPPFLAGS} -o $@ $<

clean:
	-rm -rf *.o foobar libfoobar.so daemon
