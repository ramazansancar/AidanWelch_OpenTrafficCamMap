import assert from 'assert/strict';
import standardizeDirection from '../compilation/utils/standardizeDirection.cjs';

describe('standardizeDirection()', function () {
	it('should properly standardize normal directions', () => {
		assert.equal(standardizeDirection('norTh'), 'N');
		assert.equal(standardizeDirection('SOUth'), 'S');
		assert.equal(standardizeDirection('EAST'), 'E');
		assert.equal(standardizeDirection('west'), 'W');
		assert.equal(standardizeDirection('n'), 'N');
		assert.equal(standardizeDirection('S'), 'S');
		assert.equal(standardizeDirection('e'), 'E');
		assert.equal(standardizeDirection('W'), 'W');
	});

	it('should properly standardize combined direction', () => {
		assert.equal(standardizeDirection('norTh-EAST'), 'NE');
		assert.equal(standardizeDirection('SOUth              west'), 'SW');
		assert.equal(standardizeDirection('EASTsouth'), 'SE');
		assert.equal(standardizeDirection('west:north'), 'NW');
		assert.equal(standardizeDirection('nW'), 'NW');
		assert.equal(standardizeDirection('S-e'), 'SE');
		assert.equal(standardizeDirection('eN'), 'NE');
		assert.equal(standardizeDirection('W|s'), 'SW');
	});

	it('should return input on invalid direction', () => {
		assert.equal(standardizeDirection('nor-EAT'), 'nor-EAT');
		assert.equal(standardizeDirection('SUth              we'), 'SUth              we');
		assert.equal(standardizeDirection('A'), 'A');
		assert.equal(standardizeDirection('b'), 'b');
		assert.equal(standardizeDirection('oo'), 'oo');
		assert.equal(standardizeDirection('-'), '-');
		assert.equal(standardizeDirection(''), '');
		assert.equal(standardizeDirection('  '), '  ');
	});
});