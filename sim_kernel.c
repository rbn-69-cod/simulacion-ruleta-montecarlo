// Núcleo de simulación en C (equivalente a la versión numba). Se compila automáticamente desde Python.
#include <stdint.h>
#include <string.h>

static uint64_t s0, s1;
static inline uint64_t rotl(const uint64_t x, int k) { return (x << k) | (x >> (64 - k)); }
static inline uint64_t nxt(void) {  // xoroshiro128+
    uint64_t a = s0, b = s1, r = a + b;
    b ^= a; s0 = rotl(a, 24) ^ b ^ (b << 16); s1 = rotl(b, 37);
    return r;
}
static inline double rnd(void) { return (nxt() >> 11) * (1.0 / 9007199254740992.0); }
static void seed(uint64_t x) {  // splitmix64
    for (int i = 0; i < 2; i++) {
        x += 0x9e3779b97f4a7c15ULL; uint64_t z = x;
        z = (z ^ (z >> 30)) * 0xbf58476d1ce4e5b9ULL; z = (z ^ (z >> 27)) * 0x94d049bb133111ebULL;
        z ^= z >> 31; if (i == 0) s0 = z; else s1 = z;
    }
}

static const long FIB[16] = {1,1,2,3,5,8,13,21,34,55,89,144,233,377,610,987};
#define PWIN (18.0/37.0)

// out: nsess x 4 (profit, ruined, maxdrawdown, avgstake)
void run_scenario(int strat, int B0, int limit, int nspins, int nsess, uint64_t seed0, double *out) {
    long lab[4100];
    for (int k = 0; k < nsess; k++) {
        seed(seed0 + k);
        double B = B0, peak = B, mdd = 0, ssum = 0; long nb = 0;
        long mart = 1, da = 1; int fi = 0, lo = 0, hi = 6;
        for (int i = 0; i < 6; i++) lab[i] = i + 1;
        int ruined = 0;
        for (int t = 0; t < nspins; t++) {
            if (B < 1) { ruined = 1; break; }
            long s;
            if (strat == 0) s = 1;
            else if (strat == 1) s = mart;
            else if (strat == 2) s = FIB[fi];
            else if (strat == 3) s = da;
            else if (strat == 4) {
                if (hi - lo == 0) { lo = 0; hi = 6; for (int i = 0; i < 6; i++) lab[i] = i + 1; }
                s = (hi - lo == 1) ? lab[lo] : lab[lo] + lab[hi - 1];
            } else { s = (long)(B * 0.02); if (s < 1) s = 1; }
            if (s > limit) s = limit;
            if (s > B) s = (long)B;
            if (s < 1) { ruined = 1; break; }
            ssum += s; nb++;
            int win = rnd() < PWIN;
            B += win ? s : -s;
            if (strat == 1) mart = win ? 1 : (mart * 2 > (1L << 40) ? mart : mart * 2);
            else if (strat == 2) { if (win) fi = fi >= 2 ? fi - 2 : 0; else if (fi < 15) fi++; }
            else if (strat == 3) { if (win) da = da > 1 ? da - 1 : 1; else da++; }
            else if (strat == 4) {
                if (win) { if (hi - lo >= 2) { lo++; hi--; } else lo = hi; }
                else if (hi < 4090) { lab[hi] = s; hi++; }
            }
            if (B > peak) peak = B;
            if (peak - B > mdd) mdd = peak - B;
        }
        if (B < 1) ruined = 1;
        out[4*k] = B - B0; out[4*k+1] = ruined; out[4*k+2] = mdd; out[4*k+3] = nb ? ssum / nb : 0;
    }
}
