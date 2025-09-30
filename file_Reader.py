import logging
from pathlib import Path


class FileReader:
    def read_single_file(self, work_dir, file_path):
        """读取单个文件内容"""
        try:
            work_path = Path(work_dir)
            target_file = work_path / file_path

            if not target_file.exists():
                return {
                    "status": "error",
                    "message": f"文件不存在: {file_path}",
                    "files": {}
                }

            if not target_file.is_file():
                return {
                    "status": "error",
                    "message": f"路径不是文件: {file_path}",
                    "files": {}
                }

            # 读取文件内容
            try:
                with open(target_file, 'r', encoding='utf-8') as f:
                    content = f.read()

                return {
                    "status": "success",
                    "message": f"已读取文件: {file_path}",
                    "files": {
                        file_path: {
                            'content': content,
                            'type': 'text',
                            'encoding': 'utf-8',
                            'size': len(content)
                        }
                    }
                }
            except UnicodeDecodeError:
                # 二进制文件处理
                import base64
                with open(target_file, 'rb') as f:
                    binary_content = f.read()
                encoded_content = base64.b64encode(binary_content).decode('ascii')

                return {
                    "status": "success",
                    "message": f"已读取二进制文件: {file_path}",
                    "files": {
                        file_path: {
                            'content': encoded_content,
                            'type': 'binary',
                            'encoding': 'base64',
                            'size': len(binary_content)
                        }
                    }
                }

        except Exception as e:
            logging.error(f"读取文件失败 {file_path}: {e}")
            return {
                "status": "error",
                "message": f"读取文件失败: {str(e)}",
                "files": {}
            }

    def list_folder_contents(self, work_dir, folder_path):
        """列出文件夹内容"""
        try:
            work_path = Path(work_dir)
            target_folder = work_path / folder_path if folder_path else work_path

            if not target_folder.exists():
                return {
                    "status": "error",
                    "message": f"文件夹不存在: {folder_path}",
                    "files": {}
                }

            if not target_folder.is_dir():
                return {
                    "status": "error",
                    "message": f"路径不是文件夹: {folder_path}",
                    "files": {}
                }

            # 收集文件夹内容
            contents = {
                "folders": [],
                "files": []
            }

            for item in target_folder.iterdir():
                rel_path = item.relative_to(work_path)
                if item.is_dir():
                    contents["folders"].append({
                        "name": str(rel_path),
                        "type": "directory"
                    })
                else:
                    contents["files"].append({
                        "name": str(rel_path),
                        "type": "file",
                        "size": item.stat().st_size
                    })

            message = f"文件夹 '{folder_path or 'root'}' 包含 {len(contents['folders'])} 个文件夹和 {len(contents['files'])} 个文件"

            return {
                "status": "success",
                "message": message,
                "files": {f"{folder_path or 'root'}_contents": contents}
            }

        except Exception as e:
            logging.error(f"列出文件夹内容失败 {folder_path}: {e}")
            return {
                "status": "error",
                "message": f"列出文件夹内容失败: {str(e)}",
                "files": {}
            }

    def read_all_files_in_folder(self, work_dir, folder_path):
        """读取文件夹中所有文件内容"""
        try:
            work_path = Path(work_dir)
            target_folder = work_path / folder_path if folder_path else work_path

            if not target_folder.exists():
                return {
                    "status": "error",
                    "message": f"文件夹不存在: {folder_path}",
                    "files": {}
                }

            if not target_folder.is_dir():
                return {
                    "status": "error",
                    "message": f"路径不是文件夹: {folder_path}",
                    "files": {}
                }

            # 支持的代码文件扩展名
            code_extensions = {
                '.py', '.js', '.ts', '.jsx', '.tsx', '.html', '.css',
                '.java', '.cpp', '.c', '.h', '.cs', '.php', '.rb',
                '.go', '.rs', '.swift', '.kt', '.scala', '.sh',
                '.sql', '.json', '.xml', '.yaml', '.yml', '.md',
                '.txt', '.ini', '.conf', '.cfg', '.properties'
            }

            # 支持的无扩展名文件
            extensionless_files = {
                'Dockerfile', 'Makefile', 'Jenkinsfile', 'Procfile',
                'Rakefile', 'Gemfile', 'Vagrantfile', 'Brewfile'
            }

            files_content = {}
            file_count = 0

            # 递归读取所有代码文件
            for file_path in target_folder.rglob('*'):
                # 检查是否是支持的文件：有扩展名的文件 或 特定的无扩展名文件
                has_valid_extension = file_path.suffix.lower() in code_extensions
                is_valid_extensionless = file_path.name in extensionless_files

                if file_path.is_file() and (has_valid_extension or is_valid_extensionless):
                    rel_path = file_path.relative_to(work_path)

                    try:
                        # 尝试读取文本文件
                        with open(file_path, 'r', encoding='utf-8') as f:
                            content = f.read()

                        files_content[str(rel_path)] = {
                            'content': content,
                            'type': 'text',
                            'encoding': 'utf-8',
                            'size': len(content)
                        }
                        file_count += 1

                    except UnicodeDecodeError:
                        # 二进制文件处理
                        import base64
                        with open(file_path, 'rb') as f:
                            binary_content = f.read()
                        encoded_content = base64.b64encode(binary_content).decode('ascii')

                        files_content[str(rel_path)] = {
                            'content': encoded_content,
                            'type': 'binary',
                            'encoding': 'base64',
                            'size': len(binary_content)
                        }
                        file_count += 1

                    except Exception as e:
                        logging.warning(f"读取文件失败 {rel_path}: {e}")

            message = f"已读取文件夹 '{folder_path or 'root'}' 中的 {file_count} 个文件"

            return {
                "status": "success",
                "message": message,
                "files": files_content
            }

        except Exception as e:
            logging.error(f"读取文件夹所有文件失败 {folder_path}: {e}")
            return {
                "status": "error",
                "message": f"读取文件夹所有文件失败: {str(e)}",
                "files": {}
            }

    def list_generated_folders(self, work_dir):
        """列出生成的文件夹列表"""
        try:
            work_path = Path(work_dir)

            if not work_path.exists():
                return {
                    "status": "error",
                    "message": f"工作目录不存在: {work_dir}",
                    "files": {}
                }

            folders = []
            for item in work_path.rglob('*'):
                if item.is_dir():
                    rel_path = item.relative_to(work_path)
                    # 统计文件夹中的文件数量
                    file_count = sum(1 for f in item.rglob('*') if f.is_file())

                    folders.append({
                        "name": str(rel_path),
                        "path": str(rel_path),
                        "file_count": file_count
                    })

            message = f"找到 {len(folders)} 个文件夹"

            return {
                "status": "success",
                "message": message,
                "files": {"folder_list": folders}
            }

        except Exception as e:
            logging.error(f"列出文件夹失败: {e}")
            return {
                "status": "error",
                "message": f"列出文件夹失败: {str(e)}",
                "files": {}
            }
