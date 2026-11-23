#include <stdio.h>
#include <stdlib.h>
#include <unistd.h>
int main(void) {
    unsigned int a = 0, b = 0, c = 0, d = 0;
    unsigned int e = 0, f = 0;
    int sink = 0;
    unsigned char buf[16];
    if (read(0, buf, sizeof(buf)) <= 0) return 1;
    a = (buf[0] << 8) | buf[1];
    b = (buf[2] << 8) | buf[3];
    c = (buf[4] << 8) | buf[5];
    d = (buf[6] << 8) | buf[7];
    if ((b | 5) <= 29) {
    if (b < 34) {
    if ((c * 1) <= 19) {
    if (b >= 5) {
    sink = 20 % 7;
    } else {
    sink = 26 % 7;
    }
    } else {
    if ((c ^ 13) >= 7) {
    sink = 26 % 7;
    } else {
    sink = 32 % 7;
    }
    }
    } else {
    if ((c + 2) > 20) {
    if ((b ^ 8) > 49) {
    sink = 26 % 7;
    } else {
    sink = 32 % 7;
    }
    } else {
    if ((c ^ 5) == 17) {
    sink = 32 % 7;
    } else {
    sink = 38 % 7;
    }
    }
    }
    } else {
    if (c <= 41) {
    if ((d * 11) == 45) {
    if (b != 50) {
    sink = 26 % 7;
    } else {
    sink = 32 % 7;
    }
    } else {
    if ((a >> 14) == 21) {
    sink = 32 % 7;
    } else {
    sink = 38 % 7;
    }
    }
    } else {
    if (b == 34) {
    if ((b << 1) > 59) {
    sink = 32 % 7;
    } else {
    sink = 38 % 7;
    }
    } else {
    if (d == 15) {
    sink = 38 % 7;
    } else {
    sink = 44 % 7;
    }
    }
    }
    }

    printf("%d\n", sink);
    return 0;
}
