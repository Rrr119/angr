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
    if (c == 42) {
    if (a <= 4) {
    sink = 21 % 7;
    } else {
    sink = 27 % 7;
    }
    } else {
    if (a >= 48) {
    sink = 27 % 7;
    } else {
    sink = 33 % 7;
    }
    }
    for (int i = 0; i < 3; i++) {
        if ((a + i) < 1) {
            e = e ^ (a ^ i);
        }
    }
    sink = e & 0xff;

    printf("%d\n", sink);
    return 0;
}
