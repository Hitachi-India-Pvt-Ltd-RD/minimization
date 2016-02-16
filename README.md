# The Minimization script

This Python script will generate minimized source code with the stripping techniques below.  
The minimized source tree will consist of only used source code at compile time:
* configuration conditionals such as `#ifdef` `#if` `#endif` will be eliminated.
* `#define` macros remain as are.
* `#include` sentences remain as are.
  
Currently this minimization script is applicable to Linux kernel and Busybox project.  

The minimized sources will be in more human-readable form, and it contains less lines of code.  
Such source code transformation helps us make code inspection easier and more efficient in general.  
Also, it's going to be beneficial for test or verification by having eliminated unused code.
  
The original idea comes from a post in stackoverflow.  
[Strip Linux kernel sources according to .config](http://stackoverflow.com/questions/7353640/strip-linux-kernel-sources-according-to-config)
    
## Prerequisite
The minimization script requires the following commands working in the host machine.
* `diffstat`
* `diff`
* `echo`
* `file`
* `gcc` (and everything else that is needed to build Linux Kernel or BusyBox)
* `python` (2.x and 3.x compatibility is supported)
  
# Usage 
1. Navigate to your kernel tree directory.  
example:
```bash
$ cd linux-4.4.1
```

2. copy `minimize.py` to your kernel tree directory.

3. prepare configuration file  
Prepare your tuned `.config` and put it to the kernel tree directory.  
Or generate `.config` by `make` command.  
example:
```bash
$ make allnoconfig
```

4. add the script directory path  
example:
```bash
$ export PATH=$PATH:`pwd`
```

5. run make with the following options.
```bash
$ make C=1 CHECK=minimize.py CF="-mindir ../minimized-tree/"
```
use `C=1` to perform minimization only for (re)compilation target files.  
use `C=2` to perform minimization for all the source files regardless of whether they are compilation target or not.  
specify any output directory at `-mindir` option in `CF` flag  
`C`, `CHECK` flags are mandatory. `-mindir` option in `CF` flag is optional, the default minimized tree location is `../minimized-tree` if `CF` is omitted.  
  
  
Or, minimization is also applicable for partial build target.  
example:
```bash
$ make drivers C=1 CHECK=minimize.py CF="-mindir ../minimized-tree/"
```

if successful, compilation and minimization will be executed at the same time,   
and the minimized kernel tree will be generated under `../minimized-tree/`

## BusyBox Application
The script also works with other projects provided that their Makefile support source `CHECK`(sparse by default) option via `C=1` flag.  
For example, this is directly applicable to BusyBox with exactly the same workflow.  
example:
```bash
$ wget http://busybox.net/downloads/busybox-1.24.1.tar.bz2
$ tar jxf busybox-1.24.1.tar.bz2
$ cd busybox-1.24.1
$ make defconfig
$ export PATH=$PATH:<path to minimize.py>
$ make C=1 CHECK=minimize.py CF="-mindir ../minimized-busybox/"
```
  
  
On completed, the minimized BusyBox sources will be generated under directory `../minimized-busybox/`.  
In the example above, there will be 505 C files(with NO #ifdef blocks) in the minimized tree,  
where there were originally 629 C files(with many complicated #ifdef conditional blocks).  
  
## Summary Information
There is a minimization summary info available. In the minimized tree directory, a text file `diffstat.log` and `minimize.patch` will be generated.  
If you run `minimize.py` with the filepath of `diffstat.log`, it will display summary info like this.  
```bash
$ ./minimize.py ../minimized-busybox/diffstat.log 
296 out of 505 compiled C files have been minimized.
Unused 20460 lines(11% of the original C code) have been removed.
```

## Verification for the minimized built binary
For BusyBox, you can build the minimized source tree with the same make commands.  
You can copy the minimized C files to the busybox project directory by overwriting the original ones, then make them.  
Among the minimized built products, `busybox_unstripped.out` and `busybox_unstripped.out` are exactly the same as the original ones(md5sum matches).  
The executables `busybox` and `busybox_unstripped` differ in some points(build time stamp etc),  
but the disassembled code (output of `objdump -d busybox`) exactly matches with the original ones also.  
  
For the Linux Kernel, we confirmed `objdump -d vmlinux.o` exatcly matches between the minimized and the original built product in `allnoconfig` condition.  
For compilation of the minimized Kernel Tree, `allnoconfig`, `defconfig`(x86), and cross-environment `omap2plus_defconfig`(arm-linux-gnueabi) are confirmed successful.  
For compilation of the minimized BusyBox, `allnoconfig` and `defconfig`(x86) are confirmed successful.  
Other kernel configs or architectures are yet to be determined.  
  
## TODOs
1. Consider extending this technique to other build system such as CMake.
2. Combine analysis execution at one time (like `--with-spatch` option).
3. Try other kernel/busybox config or othre architectures.

## Version compatibility
* Works on either Python 2.x or 3.x without any modification. 
* For Linux Kernel, we've confirmed 4.0.7, 4.3.3, and 4.4.1 are applicable.
* For BusyBox, we've confirmed 1.24.1 is applicable.


## Reference
* [relevant discussions in the SIL2LinuxMP mailing list](http://lists.osadl.org/pipermail/sil2linuxmp/2015-October/000142.html)


## Contact
If you have problems, questions, ideas or suggestions, please contact below, or post to the SIL2LinuxMP mailing list.
* Desai Krishnaji <krishnaji@hitachi.co.in>
* Kotaro Hashimoto <kotaro.hashimoto.jv@hitachi.com>