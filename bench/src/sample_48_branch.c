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
    if ((b + 3) <= 39) {
    if ((d | 10) <= 40) {
    if (d != 45) {
    if (b <= 50) {
    if (b > 46) {
    sink = 53 % 7;
    } else {
    sink = 59 % 7;
    }
    } else {
    if ((b + 10) == 40) {
    sink = 59 % 7;
    } else {
    sink = 65 % 7;
    }
    }
    } else {
    if ((b ^ 1) == 26) {
    if (c >= 31) {
    sink = 59 % 7;
    } else {
    sink = 65 % 7;
    }
    } else {
    if (c == 46) {
    sink = 65 % 7;
    } else {
    sink = 71 % 7;
    }
    }
    }
    } else {
    if (b >= 19) {
    if ((d - 10) == 49) {
    if ((c >> 11) >= 41) {
    sink = 59 % 7;
    } else {
    sink = 65 % 7;
    }
    } else {
    if (a == 33) {
    sink = 65 % 7;
    } else {
    sink = 71 % 7;
    }
    }
    } else {
    if (c <= 35) {
    if (c > 11) {
    sink = 65 % 7;
    } else {
    sink = 71 % 7;
    }
    } else {
    if (d < 39) {
    sink = 71 % 7;
    } else {
    sink = 77 % 7;
    }
    }
    }
    }
    } else {
    if (c != 23) {
    if ((b - 7) < 43) {
    if (a < 51) {
    if (d == 48) {
    sink = 59 % 7;
    } else {
    sink = 65 % 7;
    }
    } else {
    if (d > 19) {
    sink = 65 % 7;
    } else {
    sink = 71 % 7;
    }
    }
    } else {
    if ((b * 2) <= 2) {
    if (d >= 16) {
    sink = 65 % 7;
    } else {
    sink = 71 % 7;
    }
    } else {
    if ((b + 9) < 21) {
    sink = 71 % 7;
    } else {
    sink = 77 % 7;
    }
    }
    }
    } else {
    if ((b ^ 1) <= 49) {
    if (b < 3) {
    if ((a * 11) == 56) {
    sink = 65 % 7;
    } else {
    sink = 71 % 7;
    }
    } else {
    if (a <= 14) {
    sink = 71 % 7;
    } else {
    sink = 77 % 7;
    }
    }
    } else {
    if ((b ^ 12) == 44) {
    if (b < 44) {
    sink = 71 % 7;
    } else {
    sink = 77 % 7;
    }
    } else {
    if ((a >> 11) < 55) {
    sink = 77 % 7;
    } else {
    sink = 83 % 7;
    }
    }
    }
    }
    }

    printf("%d\n", sink);
    return 0;
}
