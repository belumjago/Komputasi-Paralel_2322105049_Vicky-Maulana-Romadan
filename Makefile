# ==============================================================================
# Makefile - Komputasi Paralel Estimasi Pi Monte Carlo
# Penulis   : Vicky Maulana Romadan (NIM: 2322105049)
# Kelas     : Komputer Paralel (Sistem Terdistribusi) - UTS Ganjil 2026/2027
# Dosen     : Dr. Ir. Antonius Irianto. S, ST., MT
# ==============================================================================

CC = gcc
CFLAGS = -O3 -Wall -Wextra -fopenmp -Iinclude
LDFLAGS = -fopenmp -lpthread -lm

BIN_DIR = bin
SRC_DIR = src
INC_DIR = include
RES_DIR = results
FIG_DIR = figures

TARGETS = $(BIN_DIR)/serial.exe $(BIN_DIR)/pthreads.exe $(BIN_DIR)/openmp.exe $(BIN_DIR)/benchmark.exe

.PHONY: all clean run-serial run-pthreads run-openmp bench plot dirs

all: dirs $(TARGETS)

dirs:
	@mkdir -p $(BIN_DIR) $(RES_DIR) $(FIG_DIR)

$(BIN_DIR)/serial.exe: $(SRC_DIR)/serial.c $(INC_DIR)/common.h
	$(CC) $(CFLAGS) $(SRC_DIR)/serial.c -o $@ $(LDFLAGS)

$(BIN_DIR)/pthreads.exe: $(SRC_DIR)/pthreads.c $(INC_DIR)/common.h
	$(CC) $(CFLAGS) $(SRC_DIR)/pthreads.c -o $@ $(LDFLAGS)

$(BIN_DIR)/openmp.exe: $(SRC_DIR)/openmp.c $(INC_DIR)/common.h
	$(CC) $(CFLAGS) $(SRC_DIR)/openmp.c -o $@ $(LDFLAGS)

$(BIN_DIR)/benchmark.exe: $(SRC_DIR)/benchmark.c $(INC_DIR)/common.h
	$(CC) $(CFLAGS) $(SRC_DIR)/benchmark.c -o $@ $(LDFLAGS)

run-serial: $(BIN_DIR)/serial.exe
	./$(BIN_DIR)/serial.exe 1000000000 0

run-pthreads: $(BIN_DIR)/pthreads.exe
	./$(BIN_DIR)/pthreads.exe 1000000000 8 0 0

run-openmp: $(BIN_DIR)/openmp.exe
	./$(BIN_DIR)/openmp.exe 1000000000 8 0 0

bench: $(BIN_DIR)/benchmark.exe
	./$(BIN_DIR)/benchmark.exe 1000000000 3

plot:
	python scripts/plot_results.py

report:
	python scripts/generate_report_pdf.py

clean:
	rm -rf $(BIN_DIR)/*.exe $(RES_DIR)/*.csv
