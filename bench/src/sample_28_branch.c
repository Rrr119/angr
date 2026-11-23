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
    if (b < 24) {
    if (c == 35) {
    if (c > 52) {
    sink = 31 % 7;
    } else {
    sink = 37 % 7;
    }
    } else {
    if (b >= 2) {
    sink = 37 % 7;
    } else {
    sink = 43 % 7;
    }
    }
    } else {
    if ((c >> 3) >= 51) {
    if (b > 3) {
    sink = 37 % 7;
    } else {
    sink = 43 % 7;
    }
    } else {
    if (b > 11) {
    sink = 43 % 7;
    } else {
    sink = 49 % 7;
    }
    }
    }

    printf("%d\n", sink);
    return 0;
}
