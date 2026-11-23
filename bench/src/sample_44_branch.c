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
    if (d <= 24) {
    if ((c - 1) < 57) {
    if ((c * 4) <= 60) {
    if (a >= 41) {
    sink = 48 % 7;
    } else {
    sink = 54 % 7;
    }
    } else {
    if (d < 35) {
    sink = 54 % 7;
    } else {
    sink = 60 % 7;
    }
    }
    } else {
    if ((b & 11) >= 34) {
    if ((b * 6) == 37) {
    sink = 54 % 7;
    } else {
    sink = 60 % 7;
    }
    } else {
    if (a <= 6) {
    sink = 60 % 7;
    } else {
    sink = 66 % 7;
    }
    }
    }
    } else {
    if (d >= 16) {
    if (b > 11) {
    if (d != 46) {
    sink = 54 % 7;
    } else {
    sink = 60 % 7;
    }
    } else {
    if (b <= 29) {
    sink = 60 % 7;
    } else {
    sink = 66 % 7;
    }
    }
    } else {
    if (c <= 29) {
    if (c >= 9) {
    sink = 60 % 7;
    } else {
    sink = 66 % 7;
    }
    } else {
    if (b == 60) {
    sink = 66 % 7;
    } else {
    sink = 72 % 7;
    }
    }
    }
    }

    printf("%d\n", sink);
    return 0;
}
