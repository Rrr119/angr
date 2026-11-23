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
    switch (a & 0x7) {
      case 0: sink = a >> 0; break;
      case 1: sink = a & 1; break;
      case 2: sink = a | 2; break;
      case 3: sink = a & 3; break;
      case 4: sink = a >> 4; break;
      default: sink = -1;
    }

    printf("%d\n", sink);
    return 0;
}
