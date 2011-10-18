LIBSRIC_DIR=../sricd/libsric

pyenv_start: pyenv_start.c
	$(CC) $^ -o $@ $(CFLAGS) $(LDFLAGS) -I $(LIBSRIC_DIR) -lsric -L $(LIBSRIC_DIR)

.PHONY: clean

clean:
	-rm -f pyenv_start
