/**
 * ============================================================================
 * Program     : serial.c
 * Deskripsi   : Estimasi Nilai Pi dengan Metode Monte Carlo (Versi Serial Baseline)
 * Mata Kuliah : Komputer Paralel (Sistem Terdistribusi)
 * Penulis     : Vicky Maulana Romadan (NIM: 2322105049)
 * Institusi   : Teknik Informatika, Universitas Cendekia Abditama
 * ============================================================================
 */

#include <stdio.h>
#include <stdlib.h>
#include <stdint.h>
#include <math.h>
#include "../include/common.h"

int main(int argc, char *argv[]) {
    uint64_t total_samples = DEFAULT_SAMPLES;
    int rng_type = 0; // 0 = Modern (Xorshift64*), 1 = POSIX rand_r LCG

    if (argc >= 2) {
        total_samples = strtoull(argv[1], NULL, 10);
    }
    if (argc >= 3) {
        rng_type = atoi(argv[2]);
    }

    printf("===================================================================\n");
    printf("   ESTIMASI NILAI PI DENGAN METODE MONTE CARLO (SERIAL BASELINE)   \n");
    printf("   Penulis : Vicky Maulana Romadan (NIM: 2322105049)              \n");
    printf("===================================================================\n");
    printf("Jumlah Titik Sampel : %llu (10^%.2f)\n", 
           (unsigned long long)total_samples, log10((double)total_samples));
    printf("Generator Acak (RNG): %s\n", 
           (rng_type == 0) ? "Modern Xorshift64*" : "POSIX rand_r (LCG)");

    uint64_t in_circle = 0;
    double t_start, t_end, t_elapsed;

    if (rng_type == 0) {
        // Modern Xorshift64* Generator
        uint64_t seed = 88172645463325252ULL;
        t_start = get_wall_time();

        for (uint64_t i = 0; i < total_samples; i++) {
            double x = rand_double_fast(&seed);
            double y = rand_double_fast(&seed);
            if (x * x + y * y <= 1.0) {
                in_circle++;
            }
        }

        t_end = get_wall_time();
    } else {
        // Standard POSIX rand_r (LCG)
        unsigned int seed = 42U;
        t_start = get_wall_time();

        for (uint64_t i = 0; i < total_samples; i++) {
            double x = rand_double_posix(&seed);
            double y = rand_double_posix(&seed);
            if (x * x + y * y <= 1.0) {
                in_circle++;
            }
        }

        t_end = get_wall_time();
    }

    t_elapsed = t_end - t_start;
    double pi_est = 4.0 * ((double)in_circle / (double)total_samples);
    double abs_error = fabs(pi_est - PI_TRUE);
    double rel_error = (abs_error / PI_TRUE) * 100.0;
    double throughput = ((double)total_samples / 1e6) / t_elapsed;

    printf("\n--- HASIL EKSEKUSI ---\n");
    printf("Titik dalam Lingkaran (M) : %llu\n", (unsigned long long)in_circle);
    printf("Estimasi Nilai Pi (pi_est): %.10f\n", pi_est);
    printf("Nilai Pi Sebenarnya       : %.10f\n", PI_TRUE);
    printf("Absolute Error            : %.10e\n", abs_error);
    printf("Relative Error (%%)        : %.6f%%\n", rel_error);
    printf("Waktu Eksekusi            : %.4f detik\n", t_elapsed);
    printf("Throughput Komputasi      : %.2f Juta Titik/detik\n", throughput);
    printf("===================================================================\n");

    return 0;
}
