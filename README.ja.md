# The Minimization script

ソースコード中の無効ブロックを削除し、コンパイル対象のみからなるソースコードを生成するPythonスクリプトです。  
minimize処理はソース中の各プリプロセッサディレクティブに以下のように作用します。
* `#ifdef`, `#if`, `#endif`などの制御構造が消え、有効なブロックのコードのみが残ります
* `#define`で定義されたマクロは展開されず元と同じ形で残ります
* `#include`文のヘッダファイルは展開されず元と同じ形で残ります
  
Minimizationスクリプトは Linux Kernel と BusyBox のみに対して適用可能です。(2016年1月25日現在)
  
Minimize処理により無効なコードが削除されることで、人によるコードレビューが効率よくできるようになります。  
また各種静的検証の前処理としてMinimization実行することで、テストケース削減やコードカバレッジ向上等の効果が期待されます。
  
Minimizationのアイディアは StackOverflow の以下の記事を元にしています。  
[Strip Linux kernel sources according to .config](http://stackoverflow.com/questions/7353640/strip-linux-kernel-sources-according-to-config)
  
## Prerequisite
Minimizationスクリプトを実行するためには以下のコマンド類がLinuxマシンで使用できることが必要です。
* `diffstat`
* `diff`
* `echo`
* `file`
* `gcc` (Linux Kernel または BuxyBox をビルドするのに必要なユーティリティ一式)
* `python` (2.x と 3.x のどちらでも実行可能)
  
# Usage 
1. minimizeを行うカーネルソースツリーのルートディレクトリに移動してください。  
例:
```bash
$ cd linux-4.4.1
```

2. `minimize.py`スクリプトをカーネルツリーのルートディレクトリにコピーしてください。

3. 適用する configuration ファイルを用意してください。  
作成済みの `.config` があればそれをカーネルツリーのルートディレクトリにコピーしてください。  
または以下のようにして `.config` を生成してください。  
例:
```bash
$ make allnoconfig
```

4. `minimize.py` スクリプトへのパスを追加してください。  
例:
```bash
$ export PATH=$PATH:`pwd`
```

5. 以下のコマンドでminimize処理を実行してください。
```bash
$ make C=1 CHECK=minimize.py CF="-mindir ../minimized-tree/"
```
`C=1`を指定すると、(再)コンパイル対象のファイルのみにminimize処理が作用します。  
`C=2`を指定すると、コンパイル対象でないものも含めた全ファイルにminimize処理が作用します。  
`CF`フラグ中の `-mindir` オプションで、minimize処理後のソースツリーが生成されるディレクトリを指定してください。省略した場合は`../minimized-tree`ディレクトリにminimize結果が生成されます。  
`C`, `CHECK` フラグは必須、`CF` フラグは省略可能です。  
  
  
`make` コマンドにターゲットを指定することで、部分ビルドの対象ファイルのみに対してminimize処理を実行することも可能です。  
driversサブディレクトリに対してminimize実行する例:
```bash
$ make drivers C=1 CHECK=minimize.py CF="-mindir ../minimized-tree/"
```
  
これにより、ビルドとminimize処理が同時に実行されます。  
minimize処理後のソースファイルは `../minimized-tree/` ディレクトリ(`CF = "-mindir ..."`で指定した場所)に生成されます。  
Minimizationが作用するのはコンパイル対象のCソースファイルのみです。includeされたヘッダ等その他のファイルはそのままの状態になっています。  

## BusyBox Application
MinimizationスクリプトはLinux Kernelだけではなく、Makefileで`CHECK`オプションがサポートされている他のプロジェクトにも適用できます。  
例えば、全く同じ手順でBuxyBoxに対するMinimizationが適用できます。  
```bash
$ wget http://busybox.net/downloads/busybox-1.24.1.tar.bz2
$ tar jxf busybox-1.24.1.tar.bz2
$ cd busybox-1.24.1
$ make defconfig
$ export PATH=$PATH:<path to minimize.py>
$ make C=1 CHECK=minimize.py CF="-mindir ../minimized-busybox/"
```
  
上記コマンドの完了後、minimizeされたBusyBoxソースコードが `../minimized-busybox/` ディレクトリに生成されています。  
この例では、元々の629ファイル中ビルド対象である505のCファイルがminimize処理されています。
  
## Summary Information
Minimization結果の統計情報と差分情報が出力ディレクトリに `diffstat.log` と `minimize.patch` のファイル名で保存されています。  
`minimize.py` スクリプトを `diffstat.log` へのファイルパスを引数に直接実行すると、Minimizationサマリ情報を以下のように出力します。  
```bash
$ ./minimize.py ../minimized-busybox/diffstat.log 
296 out of 505 compiled C files have been minimized.
Unused 20460 lines(11% of the original C code) have been removed.
```

## Verification for the minimized built binary
Minimizeしたソースコードを元と同じconfig/コマンドでビルドすることができます。  
MinimizeしたBusyBoxソースコードを元のBusyBoxプロジェクトに対してディレクトリ構造ごと上書きしてmakeしてください。  
生成される`busybox_unstripped.out` および `busybox_unstripped.out`は、minimize前にビルドしたものと全く同一(md5sumが一致)となります。  
実行ファイル `busybox` および `busybox_unstripped` についてはタイムスタンプ等が異なりバイナリは一致しませんが、`objdump -d busybox` で逆アセンブルするとその結果はminimize処理前のものと一致します。  
  
Linux Kernelに対しては vmlinux.o の逆アセンブル結果 `objdump -d vmlinux.o` がminimize前後で一致することを`allnoconfig`条件下で確認しています。  
minimize後のビルド成功を確認した設定はLinux Kernelで `allnoconfig` 、`defconfig`(x86)、そしてクロスビルド環境の`omap2plus_defconfig`(arm-linux-gnueabi)です。  
BusyBoxに対しては `allnoconfig` と `defconfig` でminimized後のソースのビルド成功を確認しています。
  
## TODOs
1. CMakeなど他のビルドシステムでも適用できるよう拡張する
2. `--with-spatch`オプションなどのように、検証ツールを同時に実行できるようにする
3. Linux Kernel/BusyBoxともに他のconfigまたはアーキテクチャでも適用できることを確認する

## Version compatibility
* Python 2.x と 3.x のいずれでもそのまま実行可能です。
* Linux Kernel は 4.0.7, 4.3.3, 4.4.1 に対して適用できることを確認しました。
* BusyBox は 1.24.1 に対して適用できることを確認しました。

## Reference
* [relevant discussions in the SIL2LinuxMP mailing list](http://lists.osadl.org/pipermail/sil2linuxmp/2015-October/000142.html)


## Contact
このスクリプトに関するお問い合わせやご提案はKrishnajiまたは橋本までご連絡ください。
* Desai Krishnaji <krishnaji@hitachi.co.in>
* Kotaro Hashimoto <kotaro.hashimoto.jv@hitachi.com>