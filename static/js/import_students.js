document.addEventListener('DOMContentLoaded', function() {
    const dropZone = document.getElementById('drop-zone');
    const fileInput = document.getElementById('csv_file');
    const fileInfo = document.getElementById('file-info');
    const fileName = document.getElementById('file-name');
    const progressContainer = document.getElementById('progress-container');
    const progressBar = document.getElementById('progress-bar');
    const progressText = document.getElementById('progress-text');
    const uploadForm = document.getElementById('upload-form');
    const uploadBtn = document.getElementById('upload-btn');

    // ドラッグ&ドロップイベントの処理
    dropZone.addEventListener('dragover', function(e) {
        e.preventDefault();
        e.stopPropagation();
        dropZone.classList.add('dragover');
    });

    dropZone.addEventListener('dragleave', function(e) {
        e.preventDefault();
        e.stopPropagation();
        dropZone.classList.remove('dragover');
    });

    dropZone.addEventListener('drop', function(e) {
        e.preventDefault();
        e.stopPropagation();
        dropZone.classList.remove('dragover');

        const files = e.dataTransfer.files;
        if (files.length > 0) {
            handleFileSelect(files[0]);
        }
    });

    // クリックでファイル選択
    dropZone.addEventListener('click', function() {
        fileInput.click();
    });

    // ファイル入力変更時の処理
    fileInput.addEventListener('change', function() {
        if (fileInput.files.length > 0) {
            handleFileSelect(fileInput.files[0]);
        }
    });

    // ファイル選択時の処理
    function handleFileSelect(file) {
        // CSVファイルのみ許可
        if (!file.name.toLowerCase().endsWith('.csv')) {
            alert('CSVファイルのみアップロード可能です。');
            return;
        }

        // ファイルサイズチェック (10MB制限)
        if (file.size > 10 * 1024 * 1024) {
            alert('ファイルサイズが大きすぎます。10MB以内のファイルを選択してください。');
            return;
        }

        // ファイル情報を表示
        fileName.textContent = file.name + ' (' + formatFileSize(file.size) + ')';
        fileInfo.style.display = 'block';

        // アップロードボタンを有効化
        uploadBtn.disabled = false;
    }

    // ファイルサイズのフォーマット
    function formatFileSize(bytes) {
        if (bytes === 0) return '0 Bytes';
        const k = 1024;
        const sizes = ['Bytes', 'KB', 'MB', 'GB'];
        const i = Math.floor(Math.log(bytes) / Math.log(k));
        return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
    }

    // フォーム送信時の処理
    uploadForm.addEventListener('submit', function(e) {
        // プログレスバーを表示
        progressContainer.style.display = 'block';
        progressBar.style.width = '0%';
        progressText.textContent = 'アップロードを開始しています...';

        // アップロードボタンを無効化
        uploadBtn.disabled = true;

        // 擬似的なプログレス表示
        let progress = 0;
        const progressInterval = setInterval(function() {
            progress += Math.random() * 15;
            if (progress > 90) {
                progress = 90;
                clearInterval(progressInterval);
                progressText.textContent = 'サーバーで処理中...';
            }
            progressBar.style.width = progress + '%';
        }, 200);

        // 実際の送信はデフォルトの動作で行う
        // 完了時の処理はページ遷移で実現
    });
});