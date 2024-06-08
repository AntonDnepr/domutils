// from dominspector
var autocalc = function (o) {
	if (parseInt(o.basecost) > 9000) {
		// Autocalc
		var leadership = {
				0:	10,
				10:	15,
				20: 20,
				30: 20,
				40: 30,
				50: 30,
				60: 30,
				75: 30,
				80: 60,
				100: 60,
				120: 80,
				150: 100,
				160: 100,
				200: 150
		}

		//Leader cost
		var ldr_cost = 0;
		if (o.leader) {
			ldr_cost = ldr_cost + parseInt(leadership[o.leader]);
		}
		if (o.inspirational) {
			ldr_cost = ldr_cost + 10*parseInt(o.inspirational);
		}
		if (o.sailingshipsize && parseInt(o.sailingshipsize) > 0) {
			ldr_cost = ldr_cost + .5 * ldr_cost;
		}

		var path1 = {
				1: 30,
				2: 90,
				3: 150,
				4: 210,
				5: 270
		}
		var path2 = {
				1: 20,
				2: 60,
				3: 100,
				4: 140,
				5: 180
		}

		// Paths cost
		var paths_cost = 0;
		var arr = [];
		var baseM = [o.F, o.A, o.W, o.E, o.S, o.D, o.N, o.G, o.B];
		if (hasRandom(o)) {
			buildRandomArrays(o, 0, arr, baseM);
			for (var rand1=0; rand1 < arr.length; rand1++) {
				arr[rand1].sort(function(a,b){return b-a});
			}
			var largest = 0;
			var smallest = 0;
			for (var rand2=0; rand2 < arr.length; rand2++) {
				var tempPathCost = 0;
				for (var rand3=0, valrand; valrand = arr[rand2][rand3];  rand3++) {
					if (rand3 == 0) {
						tempPathCost = path1[valrand];
					} else {
						tempPathCost = tempPathCost + path2[valrand];
					}
				}
				if (largest == 0) {
					largest = tempPathCost;
					smallest = tempPathCost;
				} else {
					if (tempPathCost > largest) {
						largest = tempPathCost;
					} else if (tempPathCost < smallest) {
						smallest = tempPathCost;
					}
				}
			}
			paths_cost = (largest * .75) + (smallest *.25);

		} else {
			var sortedArr = [];
			for (var oj=0; oj<baseM.length; oj++) {
				if (parseInt(baseM[oj]) > 0) {
					sortedArr.push(parseInt(baseM[oj]));
				}
			}
			sortedArr.sort(function(a,b){return b-a});
			for (var ok=0, val2; val2 = sortedArr[ok];  ok++) {
				if (ok == 0) {
					paths_cost = path1[val2];
				} else {
					paths_cost = paths_cost + path2[val2];
				}
			}
		}
		if (paths_cost > 0 && o.adept_research) {
			paths_cost = paths_cost + parseInt(o.adept_research) * 5;
		}
		if (o.inept_research) {
			paths_cost = paths_cost - 5;
		}
		if (o.fixforgebonus) {
			paths_cost = paths_cost + paths_cost*(parseInt(o.fixforgebonus)/100);
		}

		// Priest cost
		var priest = {
				1: 20,
				2: 40,
				3: 100,
				4: 140
		}
		var priest_cost = 0;
		if (o.H) {
			priest_cost = parseInt(priest[o.H]);
		}

		// Spy cost
		var spy_cost = 0;
		if ((o.spy && parseInt(o.spy) > 0)) {
			spy_cost = spy_cost + 40;
		}
		if ((o.assassin && parseInt(o.assassin) > 0)) {
			spy_cost = spy_cost + 40;
		}
		if (o.seduce && parseInt(o.seduce) > 0) {
			spy_cost = spy_cost + 60;
		} else if (o.succubus && parseInt(o.succubus) > 0) {
			spy_cost = spy_cost + 60;
		}

		var cost_array = [ldr_cost, paths_cost, priest_cost, spy_cost];
		cost_array.sort(function(a,b){return b-a});

		var cost;
		if (o.type == 'c') {
			cost = cost_array[0] + cost_array[1]/2 + cost_array[2]/2 + cost_array[3]/2;
		} else {
			cost = 0;
		}
		// Special costs
		var special_cost = 0;
		if (o.stealthy && parseInt(o.stealthy) > 0 && o.type != 'u') {
			special_cost = special_cost + 5;
		}
		if (o.autohealer && parseInt(o.autohealer) > 0 && o.type != 'u') {
			special_cost = special_cost + 50;
		}
		if (o.autodishealer && parseInt(o.autodishealer) > 0 && o.type != 'u') {
			special_cost = special_cost + 20;
		}
		o.goldcost = parseInt(cost + special_cost);
		o.goldcost = o.goldcost + parseInt(o.basecost) - 10000;
		if (o.slow_to_recruit && parseInt(o.slow_to_recruit) > 0 && o.type != 'u') {
			o.goldcost = o.goldcost * 0.9;
		}
		if (o.holy && parseInt(o.holy) > 0) {
			o.goldcost = o.goldcost * 1.3;
		}
		if (o.type == 'u') {
			o.goldcost = roundIfNeeded(o.goldcost);
		} else {
			if (o.mountmnr) {
				o.goldcost = round(o.goldcost*1.4);
				o.goldcost = roundUp(o.goldcost*1.01);
			} else {
				o.goldcost = round(o.goldcost*1.4);
			}
		}
	} else {
		o.goldcost = roundIfNeeded(o.basecost);
	}
}


var roundIfNeeded = function (num) {
	if (parseInt(num) > 30) {
		return round(num);
	}
	return Math.floor(num);
}

var round = function (num) {
	return 5*(Math.floor(num/5));
}
var roundUp = function (num) {
	return 5*(Math.ceil(num/5));
}
var hasRandom = function (o) {
	if (o.randompaths.length) {
		for (var i=0, r; r= o.randompaths[i]; i++) {
			if (r.chance == 100) {
				return true;
			}
		}
	}
	return false;
}
var buildRandomArrays = function (o, i, arr, baseM) {
	var r = o.randompaths[i];
	if (r.chance != 100) {
		i++;
		if (i == o.randompaths.length) {
			return false;
		}
		r = o.randompaths[i];
		if (r.chance != 100) {
			i++;
			if (i == o.randompaths.length) {
				return false;
			}
			r = o.randompaths[i];
			if (r.chance != 100) {
				i++;
				if (i == o.randompaths.length) {
					return false;
				}
				r = o.randompaths[i];
				if (r.chance != 100) {
					i++;
					if (i == o.randompaths.length) {
						return false;
					}
				}
			}
		}
	}
	if (r.chance == 100) {
		for (var step = 0, letter; letter = r.paths.charAt(step); step++) {
			var newM = baseM.slice(0);
			if (letter.indexOf('F') != -1) {
				if (newM[0]) {
					newM[0] = parseInt(newM[0])+parseInt(r.levels);
				} else {
					newM[0] = parseInt(r.levels);
				}
			}
			if (letter.indexOf('A') != -1) {
				if (newM[1]) {
					newM[1] = parseInt(newM[1])+parseInt(r.levels);
				} else {
					newM[1] = parseInt(r.levels);
				}
			}
			if (letter.indexOf('W') != -1) {
				if (newM[2]) {
					newM[2] = parseInt(newM[2])+parseInt(r.levels);
				} else {
					newM[2] = parseInt(r.levels);
				}
			}
			if (letter.indexOf('E') != -1) {
				if (newM[3]) {
					newM[3] = parseInt(newM[3])+parseInt(r.levels);
				} else {
					newM[3] = parseInt(r.levels);
				}
			}
			if (letter.indexOf('S') != -1) {
				if (newM[4]) {
					newM[4] = parseInt(newM[4])+parseInt(r.levels);
				} else {
					newM[4] = parseInt(r.levels);
				}
			}
			if (letter.indexOf('D') != -1) {
				if (newM[5]) {
					newM[5] = parseInt(newM[5])+parseInt(r.levels);
				} else {
					newM[5] = parseInt(r.levels);
				}
			}
			if (letter.indexOf('N') != -1) {
				if (newM[6]) {
					newM[6] = parseInt(newM[6])+parseInt(r.levels);
				} else {
					newM[6] = parseInt(r.levels);
				}
			}
			if (letter.indexOf('G') != -1) {
				if (newM[7]) {
					newM[7] = parseInt(newM[7])+parseInt(r.levels);
				} else {
					newM[7] = parseInt(r.levels);
				}
			}
			if (letter.indexOf('B') != -1) {
				if (newM[8]) {
					newM[8] = parseInt(newM[8])+parseInt(r.levels);
				} else {
					newM[8] = parseInt(r.levels);
				}
			}
			if (o.randompaths.length > i+1) {
				i++;
				if (!buildRandomArrays(o, i, arr, newM)) {
					arr.push(newM);
				}
				i--;
			} else {
				arr.push(newM);
			}
		}
	} else {
		return false;
	}
	return true;
}
