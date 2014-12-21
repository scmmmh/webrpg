import DS from 'ember-data';

export default DS.RESTAdapter.extend({
	namespace: 'api',
	headers: function() {
		var userid = sessionStorage.getItem('webrpg-userid');
		var password = sessionStorage.getItem('webrpg-password');
		return {
			'X-WebRPG-Authentication': userid + ':' + password
		};
	}.property().volatile()
});
