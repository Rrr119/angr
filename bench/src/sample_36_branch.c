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
    if (c >= 11) {
    if (d > 13) {
    if (c <= 59) {
    sink = 39 % 7;
    } else {
    sink = 45 % 7;
    }
    } else {
    if (a == 8) {
    sink = 45 % 7;
    } else {
    sink = 51 % 7;
    }
    }
    } else {
    if (b > 29) {
    if (b == 18) {
    sink = 45 % 7;
    } else {
    sink = 51 % 7;
    }
    } else {
    if (d < 44) {
    sink = 51 % 7;
    } else {
    sink = 57 % 7;
    }
    }
    }

    printf("%d\n", sink);
    return 0;
}
