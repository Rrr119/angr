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
    if (a < 4) {
    if (c < 50) {
    if (b == 16) {
    if ((b ^ 11) > 48) {
    sink = 4 % 7;
    } else {
    sink = 10 % 7;
    }
    } else {
    if (d == 5) {
    sink = 10 % 7;
    } else {
    sink = 16 % 7;
    }
    }
    } else {
    if ((a - 11) == 6) {
    if ((d | 7) >= 36) {
    sink = 10 % 7;
    } else {
    sink = 16 % 7;
    }
    } else {
    if (b <= 31) {
    sink = 16 % 7;
    } else {
    sink = 22 % 7;
    }
    }
    }
    } else {
    if ((c >> 9) >= 18) {
    if (d > 3) {
    if ((c - 15) > 3) {
    sink = 10 % 7;
    } else {
    sink = 16 % 7;
    }
    } else {
    if (c == 14) {
    sink = 16 % 7;
    } else {
    sink = 22 % 7;
    }
    }
    } else {
    if (a != 40) {
    if (b < 57) {
    sink = 16 % 7;
    } else {
    sink = 22 % 7;
    }
    } else {
    if ((d - 6) > 40) {
    sink = 22 % 7;
    } else {
    sink = 28 % 7;
    }
    }
    }
    }

    printf("%d\n", sink);
    return 0;
}
