/**
 * ============================================================================
 * Program     : pthreads.c
 * Deskripsi   : Estimasi Nilai Pi Monte Carlo Menggunakan POSIX Threads (Pthreads)
 * Mata Kuliah : Komputer Paralel (Sistem Terdistribusi)
 * Penulis     : Vicky Maulana Romadan (NIM: 2322105049)
 * Institusi   : Teknik Informatika, Universitas Cendekia Abditama
 * ============================================================================
 */

#include <stdio.h>
#include <stdlib.h>
#include <stdint.h>
#include <math.h>
#include <pthread.h>
#include "../include/common.h"

// Global accumulator for Mutex Reduction mode
static uint64_t g_mutex_in_circle = 0;
static pthread_mutex_t g_mutex = PTHREAD_MUTEX_INITIALIZER;
static int g_sync_mode = 0; // 0 = Thread-Local + Join Reduction, 1 = Mutex at Exit, 2 = Direct writing (unpadded)
static int g_rng_type = 0;  // 0 = Modern Xorshift64*, 1 = POSIX rand_r

/**
 * Worker thread routine for Pthreads parallel execution
 */
void* pthreads_worker(void* arg) {
    PthreadArg* data = (PthreadArg*)arg;
    uint64_t local_count = 0;
    uint64_t samples = data->num_samples;

    if (g_rng_type == 0) {
        // Modern Xorshift64* Generator per-thread
        uint64_t state = data->seed;
        for (uint64_t i = 0; i < samples; i++) {
            double x = rand_double_fast(&state);
            double y = rand_double_fast(&state);
            if (x * x + y * y <= 1.0) {
                local_count++;
            }
        }
        data->seed = state; // Update state if needed
    } else {
        // POSIX rand_r LCG per-thread
        unsigned int seed = (unsigned int)(data->seed & 0xFFFFFFFFU);
        for (uint64_t i = 0; i < samples; i++) {
            double x = rand_double_posix(&seed);
            double y = rand_double_posix(&seed);
            if (x * x + y * y <= 1.0) {
                local_count++;
            }
        }
        data->seed = seed;
    }

    if (g_sync_mode == 1) {
        // Mutex synchronization at thread exit
        pthread_mutex_lock(&g_mutex);
        g_mutex_in_circle += local_count;
        pthread_mutex_unlock(&g_mutex);
        data->local_in_circle = local_count;
    } else {
        // Cache-line aligned local accumulation (zero contention during computation)
        data->local_in_circle = local_count;
    }

    pthread_exit(NULL);
    return NULL;
}

int main(int argc, char *argv[]) {
    uint64_t total_samples = DEFAULT_SAMPLES;
    int num_threads = 4;
    g_sync_mode = 0;
    g_rng_type = 0;

    if (argc >= 2) total_samples = strtoull(argv[1], NULL, 10);
    if (argc >= 3) num_threads = atoi(argv[2]);
    if (argc >= 4) g_sync_mode = atoi(argv[3]);
    if (argc >= 5) g_rng_type = atoi(argv[4]);

    if (num_threads <= 0) num_threads = 1;

    printf("===================================================================\n");
    printf("     ESTIMASI NILAI PI MONTE CARLO DENGAN POSIX THREADS (PTHREADS) \n");
    printf("     Penulis : Vicky Maulana Romadan (NIM: 2322105049)            \n");
    printf("===================================================================\n");
    printf("Jumlah Titik Sampel : %llu\n", (unsigned long long)total_samples);
    printf("Jumlah Threads      : %d\n", num_threads);
    printf("Sinkronisasi        : %s\n", 
           (g_sync_mode == 0) ? "Thread-Local Padded Accumulator + Main Join Reduction" :
           (g_sync_mode == 1) ? "Mutex Atomic Lock at Thread Exit" : "Direct Memory Array");
    printf("Generator Acak (RNG): %s (Per-Thread Isolated State)\n", 
           (g_rng_type == 0) ? "Modern Xorshift64*" : "POSIX rand_r (LCG)");

    // Allocate thread handles and thread arguments
    pthread_t *threads = (pthread_t*)malloc(sizeof(pthread_t) * num_threads);
    PthreadArg *args = (PthreadArg*)malloc(sizeof(PthreadArg) * num_threads);

    if (!threads || !args) {
        fprintf(stderr, "Error: Gagal mengalokasikan memori untuk threads!\n");
        return 1;
    }

    // Workload partitioning: static block decomposition
    uint64_t base_samples = total_samples / num_threads;
    uint64_t remainder = total_samples % num_threads;

    uint64_t master_seed = 88172645463325252ULL;
    double t_start = get_wall_time();

    // Create threads
    for (int t = 0; t < num_threads; t++) {
        args[t].thread_id = t;
        args[t].total_threads = num_threads;
        args[t].num_samples = base_samples + (t < (int)remainder ? 1 : 0);
        args[t].local_in_circle = 0;
        
        // Generate independent seed using splitmix64 to prevent correlation
        uint64_t seed_input = master_seed + (uint64_t)t * 1000000007ULL;
        args[t].seed = splitmix64(&seed_input);

        int rc = pthread_create(&threads[t], NULL, pthreads_worker, (void*)&args[t]);
        if (rc) {
            fprintf(stderr, "Error: pthread_create failed with code %d\n", rc);
            return 1;
        }
    }

    // Wait for all threads to finish (pthread_join) and aggregate reduction
    uint64_t total_in_circle = 0;
    for (int t = 0; t < num_threads; t++) {
        pthread_join(threads[t], NULL);
        if (g_sync_mode == 0) {
            total_in_circle += args[t].local_in_circle;
        }
    }

    if (g_sync_mode == 1) {
        total_in_circle = g_mutex_in_circle;
    }

    double t_end = get_wall_time();
    double t_elapsed = t_end - t_start;

    double pi_est = 4.0 * ((double)total_in_circle / (double)total_samples);
    double abs_error = fabs(pi_est - PI_TRUE);
    double rel_error = (abs_error / PI_TRUE) * 100.0;
    double throughput = ((double)total_samples / 1e6) / t_elapsed;

    printf("\n--- HASIL EKSEKUSI PTHREADS ---\n");
    printf("Total Titik dalam Lingkaran: %llu\n", (unsigned long long)total_in_circle);
    printf("Estimasi Nilai Pi          : %.10f\n", pi_est);
    printf("Nilai Pi Sebenarnya        : %.10f\n", PI_TRUE);
    printf("Absolute Error             : %.10e\n", abs_error);
    printf("Relative Error (%%)         : %.6f%%\n", rel_error);
    printf("Waktu Eksekusi             : %.4f detik\n", t_elapsed);
    printf("Throughput Komputasi       : %.2f Juta Titik/detik\n", throughput);
    printf("===================================================================\n");

    free(threads);
    free(args);
    return 0;
}
