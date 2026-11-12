CC ?= cc
CFLAGS ?= -O2 -Wall
LDLIBS ?= -lfdt

all: dtbTool-exynos

dtbTool-exynos: dtbtool-exynos.o
	$(CC) $(LDFLAGS) -o $@ $^ $(LDLIBS)

clean:
	$(RM) dtbtool-exynos.o dtbTool-exynos

.PHONY: all clean
