// daily-frame: one screen. Reads history.json (every day shown, oldest first, written by tools/daily.py).
// Today's picture fills the middle; the archive lists only days before it (a picture moves there once the next day has replaced it).
// Routes: '' today, #archive, #about, #YYYY-MM-DD a past day. Left/right arrows step between days.
(function () {
	'use strict';

	// ?preview (local only: preview/history.json is not published) shows a made-up history, to check a full archive
	var PREVIEW = /[?&]preview\b/.test(location.search) && /^(localhost|127\.0\.0\.1)$/.test(location.hostname);
	var SMALL = {a: 1, an: 1, and: 1, of: 1, the: 1, in: 1, on: 1, at: 1, to: 1, for: 1, with: 1, by: 1, or: 1};
	var $ = function (id) { return document.getElementById(id); };
	var days = [];   // shown so far, oldest first; the last one is today's
	var tick = 0;

	function dublin () {
		var p = {};
		new Intl.DateTimeFormat('en-GB', {timeZone: 'Europe/Dublin', year: 'numeric', month: '2-digit', day: '2-digit', hour: '2-digit', minute: '2-digit', second: '2-digit', hourCycle: 'h23'})
			.formatToParts(new Date()).forEach(function (x) { p[x.type] = x.value; });
		return p;
	}
	function today () { var p = dublin(); return p.year + '-' + p.month + '-' + p.day; }
	function nice (iso) { return new Date(iso + 'T12:00:00Z').toLocaleDateString('en-GB', {timeZone: 'UTC', day: 'numeric', month: 'short', year: 'numeric'}); }
	function title (file) {
		return file.replace(/\.webp$/i, '').replace(/^\d+-/, '').split('-').map(function (w, i) {
			return i > 0 && SMALL[w] ? w : w.charAt(0).toUpperCase() + w.slice(1);
		}).join(' ');
	}
	function frame (file) { return 'frames/' + encodeURIComponent(file); }
	function pad (n) { return (n < 10 ? '0' : '') + n; }

	function show (view) {
		['pic', 'archive', 'about'].forEach(function (v) { $(v).hidden = v !== view; });
		[['archive-link', 'archive'], ['about-link', 'about']].forEach(function (x) {
			if (view === x[1]) $(x[0]).setAttribute('aria-current', 'page'); else $(x[0]).removeAttribute('aria-current');
		});
	}

	// the picture in the middle: today's (index = last) or a past day's
	function showDay (i) {
		var d = days[i], isToday = i === days.length - 1;
		var img = $('pic-img');
		var src = isToday && !PREVIEW ? 'latest.webp' : frame(d.file);
		if (img.getAttribute('src') !== src) { img.src = src; img.classList.remove('swap'); void img.offsetWidth; img.classList.add('swap'); }
		img.alt = title(d.file) + ', ' + nice(d.date);
		$('info').href = src;
		$('info-title').textContent = title(d.file);
		clearInterval(tick);
		if (isToday) {
			var draw = function () {
				var p = dublin(), s = 86400 - (+p.hour * 3600 + +p.minute * 60 + +p.second);
				$('info-when').textContent = d.date < today() || s <= 1 ? 'next one any minute' : 'next in ' + Math.floor(s / 3600) + ':' + pad(Math.floor(s / 60) % 60) + ':' + pad(s % 60);
			};
			draw();
			tick = setInterval(draw, 1000);
		} else {
			$('info-when').textContent = nice(d.date);
		}
		show('pic');
	}

	function buildArchive () {
		var grid = $('grid'), past = days.slice(0, -1).reverse();
		grid.textContent = '';
		$('archive-link').textContent = past.length ? 'Archive (' + past.length + ')' : 'Archive';
		var empty = $('archive-empty');
		empty.hidden = past.length > 0;
		if (!past.length) { empty.textContent = 'Empty until tomorrow. ' + title(days[days.length - 1].file) + ' is the first to arrive.'; return; }
		past.forEach(function (d) {
			var li = document.createElement('li'), a = document.createElement('a'), img = document.createElement('img'), s = document.createElement('span');
			a.href = '#' + d.date;
			img.src = 'thumbs/' + encodeURIComponent(d.file);
			img.alt = title(d.file);
			img.width = 640; img.height = 360;
			img.loading = 'lazy';
			s.textContent = title(d.file) + ' · ' + nice(d.date);
			var pr = document.createElement('span');
			pr.className = 'print';
			s.className = 'cap';
			pr.appendChild(img); a.appendChild(pr); a.appendChild(s); li.appendChild(a); grid.appendChild(li);
		});
	}

	function route () {
		if (!days.length) return;
		var h = location.hash.slice(1);
		// the archive and about keep today's picture (and its countdown) in the bottom-left corner
		if (h === 'archive' || h === 'about') { showDay(days.length - 1); show(h); return; }
		var i = -1;
		for (var k = 0; k < days.length - 1; k++) if (days[k].date === h) i = k;
		showDay(i >= 0 ? i : days.length - 1);
	}
	function current () { var h = location.hash.slice(1); for (var k = 0; k < days.length; k++) if (days[k].date === h) return k; return days.length - 1; }

	function load () {
		fetch((PREVIEW ? 'preview/history.json' : 'history.json') + '?t=' + Math.floor(Date.now() / 60000), {cache: 'no-store'})
			.then(function (r) { if (!r.ok) throw new Error(r.status); return r.json(); })
			.then(function (list) {
				var t = today();
				days = (Array.isArray(list) ? list : [])
					.filter(function (e) { return e && /^\d{4}-\d{2}-\d{2}$/.test(e.date) && /^[\w.-]+\.webp$/i.test(e.file) && e.date <= t; })
					.sort(function (a, b) { return a.date < b.date ? -1 : a.date > b.date ? 1 : 0; });
				if (!days.length) throw new Error('empty');
				buildArchive();
				route();
			})
			.catch(function () { $('info-title').textContent = 'Could not load the list of days'; $('info-when').textContent = 'reload in a minute'; });
	}

	window.addEventListener('hashchange', route);
	$('home').addEventListener('click', function (e) { e.preventDefault(); history.pushState(null, '', location.pathname + location.search); route(); });
	document.addEventListener('keydown', function (e) {
		if (!days.length || $('pic').hidden) {
			if (e.key === 'Escape' && location.hash) $('home').click();
			return;
		}
		var i = current();
		if (e.key === 'ArrowLeft' && i > 0) location.hash = days[i - 1].date;
		else if (e.key === 'ArrowRight' && i < days.length - 1) { if (i + 1 === days.length - 1) $('home').click(); else location.hash = days[i + 1].date; }
	});
	// the day changes at midnight: look for the new picture every two minutes after that
	setInterval(function () { if (days.length && days[days.length - 1].date < today()) load(); }, 120000);

	// frame picker: swaps the class set in the page head, and remembers the choice in this browser
	var swatches = document.querySelectorAll('.swatch');
	function markFrame () {
		swatches.forEach(function (b) { b.setAttribute('aria-checked', document.documentElement.classList.contains('frame-' + b.dataset.frame) ? 'true' : 'false'); });
	}
	swatches.forEach(function (b) {
		b.addEventListener('click', function () {
			var h = document.documentElement;
			['black', 'oak', 'walnut', 'white'].forEach(function (f) { h.classList.remove('frame-' + f); });
			h.classList.add('frame-' + b.dataset.frame);
			try { localStorage.setItem('tok-frame', b.dataset.frame); } catch (e) {}
			markFrame();
		});
	});
	markFrame();

	if (PREVIEW) $('preview-note').hidden = false;
	load();
})();
