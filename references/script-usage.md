# 本地脚本使用

依赖：Python 3.10 或以上。除图片工具外只使用Python标准库。先将工作目录切到本Skill文件夹，或把命令中的相对路径替换为实际绝对路径。下述输出文件/目录必须尚不存在；重试时使用新路径，原输入和旧结果都保留。

```sh
python -m pip install -r requirements.txt
python scripts/prepare_images.py references/sample-images --output image-demo-output --max-edge 1200 --quality 82 --prefix pump
```

## 输入与示例预期

输入目录只读取第一层文件；输出必须是输入目录之外的全新目录。--prefix为1–49个英文字母、数字、下划线或连字符，不能传路径。示例包含透明PNG、JPEG和动画GIF。

## 能力边界

依赖Pillow>=12.2.0,<13，本机实测12.2.0。输出WebP、原名映射与哈希；动画跳过。无Python或依赖安装权限时报告缺少执行能力，不能声称已压缩。

所有样例使用example.com及虚构资料，不能当客户实测。脚本不含遥测或付费API，不会发布内容。发现问题会写入报告，不代表执行异常；命令参数或输入格式错误返回退出码2。图片工具有文件处理失败时返回1并保留manifest；跳过动画会记录原因。
