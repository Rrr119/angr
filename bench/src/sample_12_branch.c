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
    if ((c >> 13) >= 55) {
    if ((b ^ 5) > 15) {
    if (a == 45) {
    if (c >= 57) {
    if ((b + 4) < 45) {
    sink = 17 % 7;
    } else {
    sink = 23 % 7;
    }
    } else {
    if (b < 54) {
    sink = 23 % 7;
    } else {
    sink = 29 % 7;
    }
    }
    } else {
    if ((a & 10) == 22) {
    if (c > 54) {
    sink = 23 % 7;
    } else {
    sink = 29 % 7;
    }
    } else {
    if ((b - 8) != 40) {
    sink = 29 % 7;
    } else {
    sink = 35 % 7;
    }
    }
    }
    } else {
    if ((a & 5) == 28) {
    if ((a | 2) != 58) {
    if (a > 45) {
    sink = 23 % 7;
    } else {
    sink = 29 % 7;
    }
    } else {
    if (c < 30) {
    sink = 29 % 7;
    } else {
    sink = 35 % 7;
    }
    }
    } else {
    if (a <= 17) {
    if ((d | 3) >= 21) {
    sink = 29 % 7;
    } else {
    sink = 35 % 7;
    }
    } else {
    if ((d & 3) == 21) {
    sink = 35 % 7;
    } else {
    sink = 41 % 7;
    }
    }
    }
    }
    } else {
    if (c > 49) {
    if ((a * 12) <= 27) {
    if ((b & 10) >= 2) {
    if (c != 57) {
    sink = 23 % 7;
    } else {
    sink = 29 % 7;
    }
    } else {
    if ((a & 14) < 34) {
    sink = 29 % 7;
    } else {
    sink = 35 % 7;
    }
    }
    } else {
    if ((c ^ 2) != 40) {
    if (b <= 17) {
    sink = 29 % 7;
    } else {
    sink = 35 % 7;
    }
    } else {
    if (d <= 9) {
    sink = 35 % 7;
    } else {
    sink = 41 % 7;
    }
    }
    }
    } else {
    if (a > 7) {
    if (a > 39) {
    if (a < 57) {
    sink = 29 % 7;
    } else {
    sink = 35 % 7;
    }
    } else {
    if (b > 37) {
    sink = 35 % 7;
    } else {
    sink = 41 % 7;
    }
    }
    } else {
    if (a > 16) {
    if ((c - 6) >= 9) {
    sink = 35 % 7;
    } else {
    sink = 41 % 7;
    }
    } else {
    if ((a ^ 3) != 30) {
    sink = 41 % 7;
    } else {
    sink = 47 % 7;
    }
    }
    }
    }
    }

    printf("%d\n", sink);
    return 0;
}
