        # 2. 处理所有实际存在的资源文件
        logger().info("开始处理所有实际存在的资源文件")
        output_assets_path = os.path.join(paths.get('output', ''), 'assets')
        
        # 处理每个资源目录
        for valid_asset_path in valid_asset_paths:
            # 1. 获取模块名称
            # 从路径中提取模块名称，例如从 'C:/.../assets/fhpoker' 中提取 'fhpoker'
            asset_path_parts = valid_asset_path.split(os.sep)
            module_name = None
            for i, part in enumerate(asset_path_parts):
                if part == 'assets' and i + 1 < len(asset_path_parts):
                    module_name = asset_path_parts[i + 1]
                    break
            
            if not module_name:
                # 如果没有找到assets目录，直接使用最后一个目录作为模块名
                module_name = os.path.basename(valid_asset_path)
            
            logger().debug(f"处理模块: {module_name}, 资源路径: {valid_asset_path}")
            
            # 2. 遍历原工程的目录结构，为实际存在的目录创建对应目录
            for root, dirs, files in os.walk(valid_asset_path):
                # 为当前目录创建对应的输出目录
                rel_dir = os.path.relpath(root, valid_asset_path)
                output_dir = os.path.join(output_assets_path, module_name, rel_dir)
                os.makedirs(output_dir, exist_ok=True)
                
                # 处理当前目录下的文件
                for file in files:
                    # 跳过编译后的文件
                    if (file.startswith('config.') and file.endswith('.json')) or \
                       (file.startswith('index.') and file.endswith('.js')):
                        logger().debug(f"跳过编译后的文件: {file}")
                        continue
                    
                    file_path = os.path.join(root, file)
                    # 计算相对于资源目录的路径
                    rel_path = os.path.relpath(file_path, valid_asset_path)
                    
                    # 处理不同类型的资源
                    self._processResource(file_path, rel_path, valid_asset_path, paths)
        
        logger().info("实际资源文件处理完成")
