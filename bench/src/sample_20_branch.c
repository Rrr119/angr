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
    if (c == 60) {
    if (a >= 3) {
    if (c == 32) {
    if ((d ^ 3) == 20) {
    if (b >= 34) {
    sink = 25 % 7;
    } else {
    sink = 31 % 7;
    }
    } else {
    if ((b >> 1) < 57) {
    sink = 31 % 7;
    } else {
    sink = 37 % 7;
    }
    }
    } else {
    if (b <= 17) {
    if ((a * 2) == 49) {
    sink = 31 % 7;
    } else {
    sink = 37 % 7;
    }
    } else {
    if ((d | 10) != 25) {
    sink = 37 % 7;
    } else {
    sink = 43 % 7;
    }
    }
    }
    } else {
    if ((b + 3) >= 21) {
    if ((a >> 8) == 39) {
    if (c <= 21) {
    sink = 31 % 7;
    } else {
    sink = 37 % 7;
    }
    } else {
    if (a == 47) {
    sink = 37 % 7;
    } else {
    sink = 43 % 7;
    }
    }
    } else {
    if ((d - 11) <= 36) {
    if (c == 11) {
    sink = 37 % 7;
    } else {
    sink = 43 % 7;
    }
    } else {
    if (c > 20) {
    sink = 43 % 7;
    } else {
    sink = 49 % 7;
    }
    }
    }
    }
    } else {
    if (c == 25) {
    if ((d >> 14) <= 23) {
    if ((d + 4) < 3) {
    if (c < 56) {
    sink = 31 % 7;
    } else {
    sink = 37 % 7;
    }
    } else {
    if ((a >> 15) != 35) {
    sink = 37 % 7;
    } else {
    sink = 43 % 7;
    }
    }
    } else {
    if ((b - 1) == 60) {
    if (c >= 29) {
    sink = 37 % 7;
    } else {
    sink = 43 % 7;
    }
    } else {
    if ((a + 6) <= 59) {
    sink = 43 % 7;
    } else {
    sink = 49 % 7;
    }
    }
    }
    } else {
    if ((c * 9) != 16) {
    if ((b * 4) >= 34) {
    if (c != 44) {
    sink = 37 % 7;
    } else {
    sink = 43 % 7;
    }
    } else {
    if (b > 26) {
    sink = 43 % 7;
    } else {
    sink = 49 % 7;
    }
    }
    } else {
    if (a != 48) {
    if ((d << 11) <= 45) {
    sink = 43 % 7;
    } else {
    sink = 49 % 7;
    }
    } else {
    if (c != 58) {
    sink = 49 % 7;
    } else {
    sink = 55 % 7;
    }
    }
    }
    }
    }

    printf("%d\n", sink);
    return 0;
}
