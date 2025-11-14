#!/bin/bash
# reqcache PyPI 发布脚本

set -e  # 遇到错误立即退出

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# 打印带颜色的消息
print_info() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# 检查参数
TARGET=${1:-prod}

if [ "$TARGET" != "test" ] && [ "$TARGET" != "prod" ]; then
    print_error "用法: $0 [test|prod]"
    echo "  test - 发布到 TestPyPI（测试）"
    echo "  prod - 发布到正式 PyPI"
    exit 1
fi

print_info "开始准备发布 reqcache..."

# 步骤 1: 检查构建工具
print_info "检查构建工具..."
if ! command -v python &> /dev/null; then
    print_error "Python 未安装"
    exit 1
fi

print_info "检查并安装构建工具..."
MISSING_TOOLS=0
if ! python -m build --version >/dev/null 2>&1; then
    MISSING_TOOLS=1
fi
if ! command -v twine >/dev/null 2>&1; then
    MISSING_TOOLS=1
fi

if [ "$MISSING_TOOLS" -eq 1 ]; then
    print_info "安装/升级构建工具..."
    if ! pip install --upgrade build twine -q; then
        print_error "构建工具安装/升级失败，请检查网络或手动确保已安装 build 和 twine"
        exit 1
    fi
else
    print_info "构建工具已安装"
fi

# 步骤 2: 清理旧的构建文件
print_info "清理旧的构建文件..."
rm -rf dist/ build/ *.egg-info/

# 步骤 3: 运行测试
print_info "运行测试..."
if ! python -m pytest tests/ -v --tb=short; then
    print_error "测试失败，请修复后再发布"
    exit 1
fi
print_info "✓ 所有测试通过"

# 步骤 4: 构建分发包
print_info "构建分发包..."
python -m build --no-isolation

# 处理 sdist 文件名，确保符合 PyPI 规范（reqcache-py -> reqcache_py）
for sdist in dist/reqcache-py-*.tar.gz; do
    if [ -f "$sdist" ]; then
        fixed_name="${sdist/reqcache-py/reqcache_py}"
        if [ "$sdist" != "$fixed_name" ]; then
            mv "$sdist" "$fixed_name"
        fi
    fi
done

if [ ! -d "dist" ]; then
    print_error "构建失败，dist/ 目录不存在"
    exit 1
fi

# 步骤 5: 检查构建的包
print_info "检查构建的包..."
twine check dist/*

if [ $? -ne 0 ]; then
    print_error "包检查失败"
    exit 1
fi
print_info "✓ 包检查通过"

# 步骤 6: 显示包信息
print_info "构建的包："
ls -lh dist/

# 步骤 7: 上传
if [ "$TARGET" = "test" ]; then
    print_warning "准备上传到 TestPyPI..."
    echo "请确认:"
    echo "  - 版本号是否正确"
    echo "  - README.md 是否完整"
    echo "  - 所有测试是否通过"
    read -p "继续? (y/N) " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        print_warning "取消发布"
        exit 0
    fi

    print_info "上传到 TestPyPI..."
    twine upload --repository testpypi dist/*

    if [ $? -eq 0 ]; then
        print_info "✓ 成功上传到 TestPyPI!"
        echo ""
        print_info "测试安装命令:"
        echo "  pip install --index-url https://test.pypi.org/simple/ --no-deps reqcache-py"
        echo ""
        print_info "TestPyPI 项目页面:"
        echo "  https://test.pypi.org/project/reqcache-py/"
    else
        print_error "上传失败"
        exit 1
    fi
else
    print_warning "准备上传到正式 PyPI..."
    print_warning "⚠️  这将发布到正式环境，请确认:"
    echo "  - 在 TestPyPI 测试成功"
    echo "  - 版本号正确且未被使用"
    echo "  - README.md 和文档完整"
    echo "  - 代码已提交到 GitHub"
    read -p "确认发布到正式 PyPI? (yes/N) " -r
    echo
    if [[ ! $REPLY =~ ^yes$ ]]; then
        print_warning "取消发布"
        exit 0
    fi

    print_info "上传到 PyPI..."
    twine upload dist/*

    if [ $? -eq 0 ]; then
        print_info "✓ 成功发布到 PyPI!"
        echo ""
        print_info "安装命令:"
        echo "  pip install reqcache-py"
        echo ""
        print_info "PyPI 项目页面:"
        echo "  https://pypi.org/project/reqcache-py/"
        echo ""
        print_info "别忘了创建 GitHub Release:"
        echo "  git tag v0.1.0"
        echo "  git push origin v0.1.0"
    else
        print_error "上传失败"
        exit 1
    fi
fi

print_info "完成!"
