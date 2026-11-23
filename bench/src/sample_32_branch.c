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
    if (d == 54) {
    if ((b & 14) <= 55) {
    if ((a >> 8) > 21) {
    if (d != 7) {
    if (c <= 7) {
    sink = 37 % 7;
    } else {
    sink = 43 % 7;
    }
    } else {
    if ((c * 13) < 14) {
    sink = 43 % 7;
    } else {
    sink = 49 % 7;
    }
    }
    } else {
    if (d != 42) {
    if (a != 31) {
    sink = 43 % 7;
    } else {
    sink = 49 % 7;
    }
    } else {
    if (c > 46) {
    sink = 49 % 7;
    } else {
    sink = 55 % 7;
    }
    }
    }
    } else {
    if (b <= 43) {
    if ((a >> 14) < 27) {
    if ((a & 1) == 24) {
    sink = 43 % 7;
    } else {
    sink = 49 % 7;
    }
    } else {
    if ((a >> 10) > 20) {
    sink = 49 % 7;
    } else {
    sink = 55 % 7;
    }
    }
    } else {
    if (c < 49) {
    if (d < 20) {
    sink = 49 % 7;
    } else {
    sink = 55 % 7;
    }
    } else {
    if (c != 33) {
    sink = 55 % 7;
    } else {
    sink = 61 % 7;
    }
    }
    }
    }
    } else {
    if (d >= 45) {
    if ((c - 6) != 8) {
    if ((c << 11) > 46) {
    if (a < 49) {
    sink = 43 % 7;
    } else {
    sink = 49 % 7;
    }
    } else {
    if (d <= 42) {
    sink = 49 % 7;
    } else {
    sink = 55 % 7;
    }
    }
    } else {
    if (c == 27) {
    if ((b ^ 9) == 45) {
    sink = 49 % 7;
    } else {
    sink = 55 % 7;
    }
    } else {
    if (d <= 9) {
    sink = 55 % 7;
    } else {
    sink = 61 % 7;
    }
    }
    }
    } else {
    if (c != 12) {
    if ((c << 14) < 47) {
    if (d <= 25) {
    sink = 49 % 7;
    } else {
    sink = 55 % 7;
    }
    } else {
    if ((a - 3) != 33) {
    sink = 55 % 7;
    } else {
    sink = 61 % 7;
    }
    }
    } else {
    if ((d * 14) < 13) {
    if (b < 39) {
    sink = 55 % 7;
    } else {
    sink = 61 % 7;
    }
    } else {
    if ((b + 3) == 41) {
    sink = 61 % 7;
    } else {
    sink = 67 % 7;
    }
    }
    }
    }
    }

    printf("%d\n", sink);
    return 0;
}
