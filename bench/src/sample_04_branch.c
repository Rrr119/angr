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
    if (b != 27) {
    if ((c & 11) >= 58) {
    if (d != 56) {
    if ((b * 13) != 12) {
    if ((b + 9) < 6) {
    sink = 9 % 7;
    } else {
    sink = 15 % 7;
    }
    } else {
    if (d >= 27) {
    sink = 15 % 7;
    } else {
    sink = 21 % 7;
    }
    }
    } else {
    if (c > 14) {
    if (c >= 55) {
    sink = 15 % 7;
    } else {
    sink = 21 % 7;
    }
    } else {
    if ((b ^ 8) < 20) {
    sink = 21 % 7;
    } else {
    sink = 27 % 7;
    }
    }
    }
    } else {
    if (d < 26) {
    if (d > 55) {
    if (b >= 21) {
    sink = 15 % 7;
    } else {
    sink = 21 % 7;
    }
    } else {
    if (c != 35) {
    sink = 21 % 7;
    } else {
    sink = 27 % 7;
    }
    }
    } else {
    if (c > 5) {
    if (a > 49) {
    sink = 21 % 7;
    } else {
    sink = 27 % 7;
    }
    } else {
    if ((d + 3) <= 14) {
    sink = 27 % 7;
    } else {
    sink = 33 % 7;
    }
    }
    }
    }
    } else {
    if (d > 4) {
    if (d != 35) {
    if ((c << 8) == 49) {
    if ((c | 1) != 18) {
    sink = 15 % 7;
    } else {
    sink = 21 % 7;
    }
    } else {
    if ((a >> 5) != 3) {
    sink = 21 % 7;
    } else {
    sink = 27 % 7;
    }
    }
    } else {
    if (a == 49) {
    if (a > 13) {
    sink = 21 % 7;
    } else {
    sink = 27 % 7;
    }
    } else {
    if ((a + 3) == 33) {
    sink = 27 % 7;
    } else {
    sink = 33 % 7;
    }
    }
    }
    } else {
    if ((d << 8) <= 34) {
    if ((c | 5) < 34) {
    if ((a ^ 10) < 40) {
    sink = 21 % 7;
    } else {
    sink = 27 % 7;
    }
    } else {
    if (b < 3) {
    sink = 27 % 7;
    } else {
    sink = 33 % 7;
    }
    }
    } else {
    if (b <= 8) {
    if (a >= 5) {
    sink = 27 % 7;
    } else {
    sink = 33 % 7;
    }
    } else {
    if ((d & 4) == 54) {
    sink = 33 % 7;
    } else {
    sink = 39 % 7;
    }
    }
    }
    }
    }

    printf("%d\n", sink);
    return 0;
}
