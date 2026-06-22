function tableApp(lbItems) {
    return {
        current: 1,
        lbItems: lbItems,

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

        openLightbox(idx) {
            this.lb.idx = idx;
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
    };
}
