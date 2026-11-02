/**
 * ============================================================================
 * Program     : openmp.c
 * Deskripsi   : Estimasi Nilai Pi Monte Carlo Menggunakan Compiler Directive OpenMP
 * Mata Kuliah : Komputer Paralel (Sistem Terdistribusi)
 * Penulis     : Vicky Maulana Romadan (NIM: 2322105049)
 * Institusi   : Teknik Informatika, Universitas Cendekia Abditama
 * ============================================================================
 */

#include <stdio.h>
#include <stdlib.h>
#include <stdint.h>
#include <math.h>
#include <omp.h>
#include "../include/common.h"

int main(int argc, char *argv[]) {
    uint64_t total_samples = DEFAULT_SAMPLES;
    int num_threads = 4;
    int schedule_type = 0; // 0 = static, 1 = dynamic, 2 = guided
    int rng_type = 0;      // 0 = Modern Xorshift64*, 1 = POSIX rand_r

    if (argc >= 2) total_samples = strtoull(argv[1], NULL, 10);
    if (argc >= 3) num_threads = atoi(argv[2]);
    if (argc >= 4) schedule_type = atoi(argv[3]);
    if (argc >= 5) rng_type = atoi(argv[4]);

    if (num_threads <= 0) num_threads = 1;
    omp_set_num_threads(num_threads);

    const char *sched_name = (schedule_type == 0) ? "static" :
                             (schedule_type == 1) ? "dynamic, 100000" : "guided";

    printf("===================================================================\n");
    printf("     ESTIMASI NILAI PI MONTE CARLO DENGAN OPENMP DIRECTIVES        \n");
    printf("     Penulis : Vicky Maulana Romadan (NIM: 2322105049)            \n");
    printf("===================================================================\n");
    printf("Jumlah Titik Sampel : %llu\n", (unsigned long long)total_samples);
    printf("Jumlah Threads      : %d\n", num_threads);
    printf("Scheduling Clause   : %s\n", sched_name);
    printf("Generator Acak (RNG): %s (Per-Thread Isolated Seed)\n", 
           (rng_type == 0) ? "Modern Xorshift64*" : "POSIX rand_r (LCG)");

    // Initialize per-thread RNG seeds to guarantee zero cross-thread sharing
    uint64_t *seeds_fast = (uint64_t*)malloc(sizeof(uint64_t) * num_threads * 8); // 8 to ensure padding
    unsigned int *seeds_posix = (unsigned int*)malloc(sizeof(unsigned int) * num_threads * 16);

    uint64_t master_seed = 88172645463325252ULL;
    for (int t = 0; t < num_threads; t++) {
        uint64_t input = master_seed + (uint64_t)t * 1000000007ULL;
        seeds_fast[t * 8] = splitmix64(&input);
        seeds_posix[t * 16] = (unsigned int)(splitmix64(&input) & 0xFFFFFFFFU);
    }

    uint64_t in_circle = 0;
    double t_start = omp_get_wtime();

    if (rng_type == 0) {
        // Modern Xorshift64* Generator with OpenMP
        if (schedule_type == 0) {
            #pragma omp parallel reduction(+:in_circle)
            {
                int tid = omp_get_thread_num();
                uint64_t state = seeds_fast[tid * 8];
                uint64_t local_count = 0;

                #pragma omp for schedule(static)
                for (uint64_t i = 0; i < total_samples; i++) {
                    double x = rand_double_fast(&state);
                    double y = rand_double_fast(&state);
                    if (x * x + y * y <= 1.0) {
                        local_count++;
                    }
                }
                in_circle += local_count;
            }
        } else if (schedule_type == 1) {
            #pragma omp parallel reduction(+:in_circle)
            {
                int tid = omp_get_thread_num();
                uint64_t state = seeds_fast[tid * 8];
                uint64_t local_count = 0;

                #pragma omp for schedule(dynamic, 100000)
                for (uint64_t i = 0; i < total_samples; i++) {
                    double x = rand_double_fast(&state);
                    double y = rand_double_fast(&state);
                    if (x * x + y * y <= 1.0) {
                        local_count++;
                    }
                }
                in_circle += local_count;
            }
        } else {
            #pragma omp parallel reduction(+:in_circle)
            {
                int tid = omp_get_thread_num();
                uint64_t state = seeds_fast[tid * 8];
                uint64_t local_count = 0;

                #pragma omp for schedule(guided)
                for (uint64_t i = 0; i < total_samples; i++) {
                    double x = rand_double_fast(&state);
                    double y = rand_double_fast(&state);
                    if (x * x + y * y <= 1.0) {
                        local_count++;
                    }
                }
                in_circle += local_count;
            }
        }
    } else {
        // POSIX rand_r LCG Generator with OpenMP
        #pragma omp parallel reduction(+:in_circle)
        {
            int tid = omp_get_thread_num();
            unsigned int seed = seeds_posix[tid * 16];
            uint64_t local_count = 0;

            #pragma omp for schedule(static)
            for (uint64_t i = 0; i < total_samples; i++) {
                double x = rand_double_posix(&seed);
                double y = rand_double_posix(&seed);
                if (x * x + y * y <= 1.0) {
                    local_count++;
                }
            }
            in_circle += local_count;
        }
    }

    double t_end = omp_get_wtime();
    double t_elapsed = t_end - t_start;

    double pi_est = 4.0 * ((double)in_circle / (double)total_samples);
    double abs_error = fabs(pi_est - PI_TRUE);
    double rel_error = (abs_error / PI_TRUE) * 100.0;
    double throughput = ((double)total_samples / 1e6) / t_elapsed;

    printf("\n--- HASIL EKSEKUSI OPENMP ---\n");
    printf("Total Titik dalam Lingkaran: %llu\n", (unsigned long long)in_circle);
    printf("Estimasi Nilai Pi          : %.10f\n", pi_est);
    printf("Nilai Pi Sebenarnya        : %.10f\n", PI_TRUE);
    printf("Absolute Error             : %.10e\n", abs_error);
    printf("Relative Error (%%)         : %.6f%%\n", rel_error);
    printf("Waktu Eksekusi             : %.4f detik\n", t_elapsed);
    printf("Throughput Komputasi       : %.2f Juta Titik/detik\n", throughput);
    printf("===================================================================\n");

    free(seeds_fast);
    free(seeds_posix);
    return 0;
}
