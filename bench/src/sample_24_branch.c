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
    if ((c ^ 15) >= 54) {
    if (b < 16) {
    if ((d ^ 3) >= 17) {
    sink = 27 % 7;
    } else {
    sink = 33 % 7;
    }
    } else {
    if ((b & 7) <= 27) {
    sink = 33 % 7;
    } else {
    sink = 39 % 7;
    }
    }
    } else {
    if (b >= 5) {
    if (c <= 48) {
    sink = 33 % 7;
    } else {
    sink = 39 % 7;
    }
    } else {
    if ((c + 2) != 4) {
    sink = 39 % 7;
    } else {
    sink = 45 % 7;
    }
    }
    }

    printf("%d\n", sink);
    return 0;
}
