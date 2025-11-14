# 发布 reqcache 到 PyPI 指南

## 前置准备

### 1. 注册 PyPI 账号

如果还没有 PyPI 账号，需要先注册：

- **PyPI 正式仓库**: https://pypi.org/account/register/
- **TestPyPI 测试仓库**: https://test.pypi.org/account/register/

建议先在 TestPyPI 测试，成功后再发布到正式 PyPI。

### 2. 生成 API Token

1. 登录 PyPI: https://pypi.org
2. 进入账号设置: https://pypi.org/manage/account/
3. 滚动到 "API tokens" 部分
4. 点击 "Add API token"
5. 给 token 起个名字（如 "reqcache-upload"）
6. 选择 Scope: "Entire account" 或创建项目后选择特定项目
7. 点击 "Add token"
8. **重要**: 立即复制并保存 token（只显示一次！）

### 3. 配置 PyPI 凭据

创建或编辑 `~/.pypirc` 文件：

```ini
[distutils]
index-servers =
    pypi
    testpypi

[pypi]
username = __token__
password = pypi-AgEIcHlwaS5vcmcC...你的token...

[testpypi]
repository = https://test.pypi.org/legacy/
username = __token__
password = pypi-AgENdGVzdC5weXBpLm9yZwI...你的token...
```

或者使用环境变量（更安全）：
```bash
export TWINE_USERNAME=__token__
export TWINE_PASSWORD=pypi-AgEIcHlwaS5vcmcC...你的token...
```

## 发布步骤

### 步骤 1: 安装构建工具

```bash
pip install --upgrade build twine
```

### 步骤 2: 清理旧的构建文件

```bash
rm -rf dist/ build/ *.egg-info/
```

### 步骤 3: 构建分发包

```bash
python -m build
```

这会在 `dist/` 目录创建两个文件：
- `reqcache-0.1.0-py3-none-any.whl` (wheel 格式)
- `reqcache-0.1.0.tar.gz` (源码包)

### 步骤 4: 检查构建的包

```bash
twine check dist/*
```

### 步骤 5: 上传到 TestPyPI（测试）

**强烈建议先测试：**

```bash
twine upload --repository testpypi dist/*
```

### 步骤 6: 从 TestPyPI 安装测试

```bash
pip install --index-url https://test.pypi.org/simple/ --no-deps reqcache
```

测试安装的包：
```bash
python -c "import reqcache; print(reqcache.__version__)"
```

### 步骤 7: 上传到正式 PyPI

**确认测试无误后：**

```bash
twine upload dist/*
```

### 步骤 8: 验证安装

```bash
pip install reqcache
python -c "import reqcache; print(reqcache.__version__)"
```

## 快速脚本

使用提供的 `publish.sh` 脚本一键发布：

```bash
# 发布到 TestPyPI（测试）
bash publish.sh test

# 发布到正式 PyPI
bash publish.sh prod
```

## 版本管理

发布新版本时：

1. 更新 `pyproject.toml` 中的版本号：
   ```toml
   version = "0.1.1"
   ```

2. 更新 `reqcache/__init__.py` 中的版本号：
   ```python
   __version__ = "0.1.1"
   ```

3. 提交代码：
   ```bash
   git add .
   git commit -m "Bump version to 0.1.1"
   git tag v0.1.1
   git push origin main --tags
   ```

4. 重新构建和发布

## 常见问题

### 问题 1: "The user 'username' isn't allowed to upload to project 'reqcache'"

**解决方案**:
- 如果是首次发布，确保包名在 PyPI 上未被占用
- 如果包已存在，确保你有上传权限
- 检查 API token 是否正确

### 问题 2: "HTTPError: 403 Forbidden"

**解决方案**:
- 检查 API token 是否正确配置
- 确认 token 未过期
- 确认使用的是 `__token__` 作为用户名（不是你的 PyPI 用户名）

### 问题 3: "File already exists"

**解决方案**:
- PyPI 不允许重新上传相同版本
- 需要增加版本号（如从 0.1.0 到 0.1.1）

### 问题 4: 包名已被占用

**解决方案**:
- 在 `pyproject.toml` 中修改包名（如改为 `reqcache2` 或 `reqcache-plus`）
- 或联系原作者申请转让

## 项目链接

发布成功后的链接：

- **PyPI 页面**: https://pypi.org/project/reqcache/
- **安装命令**: `pip install reqcache`
- **GitHub**: https://github.com/wangys-kits/reqcache

## 徽章（Badge）

发布成功后可以在 README.md 中添加这些徽章：

```markdown
[![PyPI version](https://badge.fury.io/py/reqcache.svg)](https://badge.fury.io/py/reqcache)
[![Python versions](https://img.shields.io/pypi/pyversions/reqcache.svg)](https://pypi.org/project/reqcache/)
[![Downloads](https://pepy.tech/badge/reqcache)](https://pepy.tech/project/reqcache)
[![License](https://img.shields.io/pypi/l/reqcache.svg)](https://github.com/wangys-kits/reqcache/blob/main/LICENSE)
```

## 自动化发布（GitHub Actions）

未来可以配置 GitHub Actions 自动发布，参考 `.github/workflows/publish.yml`。
