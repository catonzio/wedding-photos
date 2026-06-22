function weddingApp(token) {
    return {
        token: token,
        activeTab: 'tavoli',

        // Gallery
        gallery: [],
        galleryLoading: false,

        // Lightbox
        lbItems: [],
        lb: {
            open: false, idx: 0,
            scale: 1, tx: 0, ty: 0,
            dragging: false,
            _ox: 0, _oy: 0,
            _pd: 0, _ps: 1,
            _sx: 0, _sy: 0,
            _lastTap: 0,
            scrollY: 0,
        },

        // Dialog
        dialogOpen: false,
        dialogStep: 'identity',   // 'identity' | 'file' | 'uploading' | 'done'

        // Snackbar
        snackbar: false,
        snackbarMsg: '',
        _snackbarTimer: null,

        // Identity step
        guestName: '',
        guestSurname: '',
        identityError: '',
        identityLoading: false,

        // File step
        selectedFiles: [],
        fileError: '',
        uploading: false,
        uploadProgress: [],
        uploadDone: 0,
        uploadTotal: 0,
        totalPercent: 0,

        // ── Init ────────────────────────────────────────────────────────
        init() {
            this.guestName = localStorage.getItem('wedding_guest_name') || '';
            this.guestSurname = localStorage.getItem('wedding_guest_surname') || '';

            const requestedTab = this._getTabFromUrl();
            this.activeTab = requestedTab;
            this._setTabInUrl(requestedTab);
            if (requestedTab === 'foto') {
                this.loadGallery();
            }
        },

        // ── Tab helpers ─────────────────────────────────────────────────
        activateTables() {
            this.activeTab = 'tavoli';
            this._setTabInUrl('tavoli');
        },

        activateGallery() {
            this.activeTab = 'foto';
            this._setTabInUrl('foto');
            this.loadGallery();
        },

        _getTabFromUrl() {
            const tab = new URLSearchParams(window.location.search).get('tab');
            return tab === 'foto' ? 'foto' : 'tavoli';
        },

        _setTabInUrl(tab) {
            const url = new URL(window.location.href);
            url.searchParams.set('tab', tab === 'foto' ? 'foto' : 'tavoli');
            window.history.replaceState({}, '', url.toString());
        },

        // ── Gallery ─────────────────────────────────────────────────────
        async loadGallery() {
            this.galleryLoading = true;
            try {
                const res = await fetch(`/wedding-photos/api/uploads?t=${encodeURIComponent(this.token)}`);
                if (res.ok) {
                    this.gallery = await res.json();
                }
            } catch (e) {
                console.error('Gallery load error', e);
            } finally {
                this.galleryLoading = false;
            }
        },

        openLightbox(item) {
            const idx = this.gallery.indexOf(item);
            this.lbItems = this.gallery.map(g => ({
                src: g.media_url,
                type: g.mime_type.startsWith('video/') ? 'video' : 'image',
                alt: g.guest_name,
            }));
            this.lb.idx = idx >= 0 ? idx : 0;
            this.lb.scale = 1; this.lb.tx = 0; this.lb.ty = 0;
            this.lb.open = true;
            this.lb.scrollY = window.scrollY;
            document.body.style.position = 'fixed';
            document.body.style.top = `-${this.lb.scrollY}px`;
            document.body.style.overflow = 'hidden';
            document.body.style.width = '100%';
        },
        closeLightbox() {
            this.lb.open = false;
            document.body.style.position = '';
            document.body.style.top = '';
            document.body.style.overflow = '';
            document.body.style.width = '';
            window.scrollTo(0, this.lb.scrollY);
        },
        lbNext() {
            this.lb.idx = (this.lb.idx + 1) % this.lbItems.length;
            this.lb.scale = 1; this.lb.tx = 0; this.lb.ty = 0;
        },
        lbPrev() {
            this.lb.idx = (this.lb.idx - 1 + this.lbItems.length) % this.lbItems.length;
            this.lb.scale = 1; this.lb.tx = 0; this.lb.ty = 0;
        },
        onLbWheel(e) {
            if (this.lbItems[this.lb.idx]?.type === 'video') return;
            e.preventDefault();
            const f = e.deltaY < 0 ? 1.15 : 1 / 1.15;
            this.lb.scale = Math.max(1, Math.min(8, this.lb.scale * f));
            if (this.lb.scale <= 1) { this.lb.tx = 0; this.lb.ty = 0; }
        },
        lbDragStart(e) {
            if (this.lb.scale <= 1) return;
            this.lb.dragging = true;
            this.lb._ox = e.clientX - this.lb.tx;
            this.lb._oy = e.clientY - this.lb.ty;
        },
        lbDragMove(e) {
            if (!this.lb.dragging) return;
            this.lb.tx = e.clientX - this.lb._ox;
            this.lb.ty = e.clientY - this.lb._oy;
        },
        lbDragEnd() { this.lb.dragging = false; },
        lbTouchStart(e) {
            const isVideo = this.lbItems[this.lb.idx]?.type === 'video';
            if (e.touches.length === 2 && !isVideo) {
                this.lb._pd = Math.hypot(
                    e.touches[0].clientX - e.touches[1].clientX,
                    e.touches[0].clientY - e.touches[1].clientY
                );
                this.lb._ps = this.lb.scale;
            } else if (e.touches.length === 1) {
                this.lb._sx = e.touches[0].clientX;
                this.lb._sy = e.touches[0].clientY;
                if (this.lb.scale > 1 && !isVideo) {
                    this.lb.dragging = true;
                    this.lb._ox = e.touches[0].clientX - this.lb.tx;
                    this.lb._oy = e.touches[0].clientY - this.lb.ty;
                }
            }
        },
        lbTouchMove(e) {
            const isVideo = this.lbItems[this.lb.idx]?.type === 'video';
            if (!isVideo) e.preventDefault();
            if (isVideo) return;
            if (e.touches.length === 2) {
                const d = Math.hypot(
                    e.touches[0].clientX - e.touches[1].clientX,
                    e.touches[0].clientY - e.touches[1].clientY
                );
                this.lb.scale = Math.max(1, Math.min(8, this.lb._ps * d / this.lb._pd));
                if (this.lb.scale <= 1) { this.lb.tx = 0; this.lb.ty = 0; }
            } else if (e.touches.length === 1 && this.lb.dragging) {
                this.lb.tx = e.touches[0].clientX - this.lb._ox;
                this.lb.ty = e.touches[0].clientY - this.lb._oy;
            }
        },
        lbTouchEnd(e) {
            this.lb.dragging = false;
            if (e.changedTouches.length === 1) {
                const dx = e.changedTouches[0].clientX - this.lb._sx;
                const dy = e.changedTouches[0].clientY - this.lb._sy;
                const now = Date.now();
                const isQuick = Math.abs(dx) < 15 && Math.abs(dy) < 15;
                if (isQuick && now - this.lb._lastTap < 300) {
                    if (this.lbItems[this.lb.idx]?.type === 'image') {
                        if (this.lb.scale > 1) {
                            this.lb.scale = 1; this.lb.tx = 0; this.lb.ty = 0;
                        } else {
                            this.lb.scale = 2.5;
                        }
                    }
                    this.lb._lastTap = 0;
                } else {
                    if (isQuick) this.lb._lastTap = now;
                    if (this.lb.scale <= 1 && Math.abs(dx) > 55 && Math.abs(dx) > Math.abs(dy) * 1.5) {
                        dx < 0 ? this.lbNext() : this.lbPrev();
                    }
                }
            }
        },

        // ── Snackbar ────────────────────────────────────────────────────
        showSnackbar(msg) {
            this.snackbarMsg = msg;
            this.snackbar = true;
            clearTimeout(this._snackbarTimer);
            this._snackbarTimer = setTimeout(() => { this.snackbar = false; }, 3000);
        },

        // ── Try-close (respects upload lock) ────────────────────────────
        tryCloseDialog() {
            if (this.dialogStep === 'uploading') {
                this.showSnackbar('Attendi il completamento del caricamento.');
                return;
            }
            this.closeDialog();
        },

        // ── Upload dialog ───────────────────────────────────────────────
        openDialog() {
            this.identityError = '';
            this.fileError = '';
            this.selectedFiles = [];
            this.uploadProgress = [];
            this.uploading = false;

            const savedName = localStorage.getItem('wedding_guest_name');
            const savedSurname = localStorage.getItem('wedding_guest_surname');
            if (savedName && savedSurname) {
                this.guestName = savedName;
                this.guestSurname = savedSurname;
                this.dialogStep = 'file';
            } else {
                this.dialogStep = 'identity';
            }
            this._dialogScrollY = window.scrollY;
            document.body.style.position = 'fixed';
            document.body.style.top = `-${this._dialogScrollY}px`;
            document.body.style.overflow = 'hidden';
            document.body.style.width = '100%';
            this.dialogOpen = true;
        },

        closeDialog() {
            this.dialogOpen = false;
            document.body.style.position = '';
            document.body.style.top = '';
            document.body.style.overflow = '';
            document.body.style.width = '';
            window.scrollTo(0, this._dialogScrollY || 0);
            if (this.dialogStep === 'done') {
                this.loadGallery();
            }
        },

        // ── Step 1: validate identity ───────────────────────────────────
        async validateIdentity() {
            this.identityError = '';
            if (!this.guestName.trim() || !this.guestSurname.trim()) {
                this.identityError = 'Inserisci nome e cognome.';
                return;
            }
            this.identityLoading = true;
            try {
                const res = await fetch(`/wedding-photos/api/guests/validate?t=${encodeURIComponent(this.token)}`, {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ name: this.guestName.trim(), surname: this.guestSurname.trim() }),
                });
                if (res.ok) {
                    localStorage.setItem('wedding_guest_name', this.guestName.trim());
                    localStorage.setItem('wedding_guest_surname', this.guestSurname.trim());
                    this.dialogStep = 'file';
                } else {
                    const data = await res.json().catch(() => ({}));
                    this.identityError = data.detail || 'Nome o cognome non trovati nella lista degli invitati.';
                }
            } catch (e) {
                this.identityError = 'Errore di rete. Riprova.';
            } finally {
                this.identityLoading = false;
            }
        },

        // ── Step 2: file selection ──────────────────────────────────────
        onFilesSelected(event) {
            this.fileError = '';
            const all = Array.from(event.target.files || []);
            const tooBig = all.filter(f => f.size > 50 * 1024 * 1024);
            if (tooBig.length > 0) {
                this.fileError = `File troppo grandi (max 50 MB): ${tooBig.map(f => f.name).join(', ')}`;
            }
            this.selectedFiles = all.filter(f => f.size <= 50 * 1024 * 1024);
        },

        formatSize(bytes) {
            if (bytes < 1024 * 1024) return (bytes / 1024).toFixed(0) + ' KB';
            return (bytes / (1024 * 1024)).toFixed(1) + ' MB';
        },

        // ── Step 3: upload ──────────────────────────────────────────────
        async startUpload() {
            if (this.selectedFiles.length === 0 || this.uploading) return;
            this.fileError = '';
            this.uploading = true;
            this.dialogStep = 'uploading';
            this.uploadDone = 0;
            this.uploadTotal = this.selectedFiles.length;
            this.totalPercent = 0;
            // track per-file progress for combined calculation
            const perFile = this.selectedFiles.map(() => 0);

            let allOk = true;
            for (let i = 0; i < this.selectedFiles.length; i++) {
                const ok = await this._uploadOne(this.selectedFiles[i], i, perFile);
                if (!ok) allOk = false;
                this.uploadDone = i + 1;
                perFile[i] = 100;
                this.totalPercent = Math.round(perFile.reduce((s, v) => s + v, 0) / this.uploadTotal);
            }

            this.uploading = false;
            if (allOk) {
                this.dialogStep = 'done';
            } else {
                this.dialogStep = 'file';
                this.fileError = 'Alcuni file non sono stati caricati. Riprova.';
            }
        },

        _uploadOne(file, index, perFile) {
            return new Promise((resolve) => {
                const formData = new FormData();
                formData.append('name', this.guestName.trim());
                formData.append('surname', this.guestSurname.trim());
                formData.append('file', file);

                const xhr = new XMLHttpRequest();
                xhr.open('POST', `/wedding-photos/api/uploads?t=${encodeURIComponent(this.token)}`);

                xhr.upload.addEventListener('progress', (e) => {
                    if (e.lengthComputable) {
                        perFile[index] = Math.round((e.loaded / e.total) * 100);
                        this.totalPercent = Math.round(perFile.reduce((s, v) => s + v, 0) / this.uploadTotal);
                    }
                });

                xhr.addEventListener('load', () => {
                    resolve(xhr.status >= 200 && xhr.status < 300);
                });

                xhr.addEventListener('error', () => resolve(false));
                xhr.send(formData);
            });
        },
    };
}
