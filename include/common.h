#ifndef COMMON_H
#define COMMON_H

#include <stdio.h>
#include <stdlib.h>
#include <stdint.h>
#include <stdbool.h>
#include <math.h>

#ifdef _WIN32
#include <windows.h>
#else
#include <time.h>
#include <sys/time.h>
#endif

#define PI_TRUE 3.1415926535897932384626433832795028841971693993751058209749445923078164
#define DEFAULT_SAMPLES 1000000000ULL /* 1 Billion samples (10^9) */
#define CACHE_LINE_SIZE 64

/**
 * High-resolution wall-clock timer returning seconds as double.
 */
static inline double get_wall_time(void) {
#ifdef _WIN32
    static LARGE_INTEGER freq;
    static int initialized = 0;
    if (!initialized) {
        QueryPerformanceFrequency(&freq);
        initialized = 1;
    }
    LARGE_INTEGER counter;
    QueryPerformanceCounter(&counter);
    return (double)counter.QuadPart / (double)freq.QuadPart;
#else
    struct timespec ts;
    clock_gettime(CLOCK_MONOTONIC, &ts);
    return (double)ts.tv_sec + (double)ts.tv_nsec * 1e-9;
#endif
}

/**
 * Xorshift64* Pseudo-Random Number Generator.
 * Period: 2^64 - 1 (~1.8 * 10^19).
 * Extremely fast, excellent statistical properties for Monte Carlo.
 */
static inline uint64_t xorshift64star(uint64_t *state) {
    uint64_t x = *state;
    x ^= x >> 12;
    x ^= x << 25;
    x ^= x >> 27;
    *state = x;
    return x * 0x2545F4914F6CDD1DULL;
}

/**
 * Generate a double in [0.0, 1.0) using 53 bits of precision from xorshift64*.
 */
static inline double rand_double_fast(uint64_t *state) {
    return (double)(xorshift64star(state) >> 11) * (1.0 / 9007199254740992.0);
}

/**
 * Portable POSIX rand_r() implementation using standard Linear Congruential Generator (LCG).
 * Period: 2^31 - 1. Provided for baseline/comparison with standard POSIX threads.
 */
static inline int portable_rand_r(unsigned int *seed) {
    *seed = *seed * 1103515245U + 12345U;
    return (int)((*seed / 65536U) % 32768U);
}

static inline double rand_double_posix(unsigned int *seed) {
    return (double)portable_rand_r(seed) / 32767.0;
}

/**
 * SplitMix64 hash generator to initialize independent seeds per thread.
 */
static inline uint64_t splitmix64(uint64_t *x) {
    uint64_t z = (*x += 0x9E3779B97F4A7C15ULL);
    z = (z ^ (z >> 30)) * 0xBF58476D1CE4E5B9ULL;
    z = (z ^ (z >> 27)) * 0x94D049BB133111EBULL;
    return z ^ (z >> 31);
}

/**
 * Pthread Worker Argument Structure.
 * Includes padding to 64 bytes (cache line size) to completely eliminate False Sharing.
 */
typedef struct {
    int thread_id;
    int total_threads;
    uint64_t num_samples;
    uint64_t local_in_circle;
    uint64_t seed;
    /* Explicit padding to guarantee each thread struct resides on its own L1/L2 cache line */
    char padding[CACHE_LINE_SIZE - ((sizeof(int)*2 + sizeof(uint64_t)*3) % CACHE_LINE_SIZE)];
} PthreadArg;

/**
 * Unpadded struct for false-sharing demonstration / anomaly analysis.
 */
typedef struct {
    int thread_id;
    int total_threads;
    uint64_t num_samples;
    uint64_t local_in_circle;
    uint64_t seed;
} PthreadArgUnpadded;

#endif /* COMMON_H */
