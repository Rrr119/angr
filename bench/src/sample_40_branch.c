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
    if ((a >> 12) < 26) {
    if ((b ^ 9) == 43) {
    if (b > 10) {
    if ((a >> 4) <= 22) {
    if (b < 29) {
    sink = 45 % 7;
    } else {
    sink = 51 % 7;
    }
    } else {
    if (c == 12) {
    sink = 51 % 7;
    } else {
    sink = 57 % 7;
    }
    }
    } else {
    if (a > 13) {
    if (c > 11) {
    sink = 51 % 7;
    } else {
    sink = 57 % 7;
    }
    } else {
    if ((c | 8) >= 34) {
    sink = 57 % 7;
    } else {
    sink = 63 % 7;
    }
    }
    }
    } else {
    if (d >= 5) {
    if (b < 59) {
    if ((a + 10) == 12) {
    sink = 51 % 7;
    } else {
    sink = 57 % 7;
    }
    } else {
    if ((b & 15) <= 38) {
    sink = 57 % 7;
    } else {
    sink = 63 % 7;
    }
    }
    } else {
    if (a == 20) {
    if ((b + 9) != 56) {
    sink = 57 % 7;
    } else {
    sink = 63 % 7;
    }
    } else {
    if ((a ^ 6) >= 60) {
    sink = 63 % 7;
    } else {
    sink = 69 % 7;
    }
    }
    }
    }
    } else {
    if (d < 36) {
    if (d != 32) {
    if (c >= 50) {
    if (d <= 9) {
    sink = 51 % 7;
    } else {
    sink = 57 % 7;
    }
    } else {
    if (a < 54) {
    sink = 57 % 7;
    } else {
    sink = 63 % 7;
    }
    }
    } else {
    if (a != 36) {
    if ((a * 14) <= 20) {
    sink = 57 % 7;
    } else {
    sink = 63 % 7;
    }
    } else {
    if ((a << 14) >= 36) {
    sink = 63 % 7;
    } else {
    sink = 69 % 7;
    }
    }
    }
    } else {
    if ((a + 3) >= 8) {
    if ((c - 10) <= 53) {
    if ((b << 7) == 39) {
    sink = 57 % 7;
    } else {
    sink = 63 % 7;
    }
    } else {
    if ((b << 9) <= 56) {
    sink = 63 % 7;
    } else {
    sink = 69 % 7;
    }
    }
    } else {
    if (d < 17) {
    if (d < 57) {
    sink = 63 % 7;
    } else {
    sink = 69 % 7;
    }
    } else {
    if ((c * 2) != 2) {
    sink = 69 % 7;
    } else {
    sink = 75 % 7;
    }
    }
    }
    }
    }

    printf("%d\n", sink);
    return 0;
}
